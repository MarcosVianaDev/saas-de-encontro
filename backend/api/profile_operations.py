import uuid
from django.db import transaction
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.http import FileResponse, Http404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from PIL import Image, UnidentifiedImageError
from apps.accounts.models import UserProfile
from apps.audit.services import record
from apps.profiles.models import ParticipantPhoto, EventOutfitPhoto, ParticipantFieldValue
from apps.participants.models import EventParticipant
from apps.notifications.models import Notification
from apps.events.permissions import require
from .event_admin import access
from .services import current, bootstrap, ordered_photos, ensure_writable, match_for, blocked


def validate_activation(p):
    profile = p.profile
    public = p.photos.filter(removed_at__isnull=True,visibility='PRE_MATCH')
    if public.count()!=3 or public.filter(is_primary=True).count()!=1:
        raise ValidationError('São necessárias três fotos públicas válidas, uma principal e a foto de outfit capturada pela equipe.')
    if not p.event.auto_activate_participants and not getattr(p, 'outfit_photo', None):
        raise ValidationError('É necessária a foto de outfit capturada pela equipe.')
    if not profile.first_name or not profile.last_name or not profile.birth_month or not profile.birth_year or not profile.gender or len(profile.bio.strip())<50:
        raise ValidationError('Complete os campos obrigatórios do perfil.')
    for field in p.event.profile_fields.filter(is_required=True):
        value=p.field_values.filter(field=field).first()
        if not value or not value.value or (field.kind=='consent' and value.value.get('accepted') is not True):
            raise ValidationError('Preencha os campos obrigatórios e aceite os termos apresentados.')
        if p.event.auto_activate_participants and field.kind != 'consent' and not str(value.value.get('answer') or '').strip():
            raise ValidationError(f'Preencha o campo obrigatório: {field.name}.')
    if p.event.mode!='ONLINE' and not p.location_consent:
        raise ValidationError('Valide a localização antes da ativação presencial.')


class ActivationView(APIView):
    @transaction.atomic
    def post(self,request,participant_id):
        member=access(request); require(member,'activation')
        p=get_object_or_404(EventParticipant.objects.select_for_update(),pk=participant_id,event=member.event)
        ensure_writable(p)
        if p.event.state not in ['OPEN','RUNNING']:
            raise PermissionDenied('A ativação está disponível em Aberto ou Em andamento.')
        from apps.moderation.models import UserSuspension
        if not p.user.is_active or UserSuspension.objects.filter(user=p.user).filter(Q(ends_at__isnull=True)|Q(ends_at__gt=timezone.now())).exists():
            raise PermissionDenied('A conta está suspensa. A ativação local não remove uma restrição global.')
        if p.active_ban or p.event_suspensions.filter(revoked_at__isnull=True).filter(Q(ends_at__isnull=True)|Q(ends_at__gt=timezone.now())).exists():
            raise PermissionDenied('Resolva a sanção antes de ativar o perfil.')
        validate_activation(p)
        p.is_active=True;p.registration_status='ACTIVE';p.deactivation_reason='';p.activated_at=p.activated_at or timezone.now();p.onboarding_completed_at=p.onboarding_completed_at or timezone.now();p.save()
        record(request.user,'profile.activated',p,p.event)
        Notification.objects.create(participant=p,event=p.event,title='Seu perfil foi ativado',body='Consulte o estado do evento para começar a descobrir participantes.')
        return Response({'ok':True})


def validated_image(upload):
    if upload is None or upload.size>10*1024*1024: raise ValidationError('Envie uma imagem de até 10 MB.')
    try:
        image=Image.open(upload)
        if image.format not in ['JPEG','PNG','WEBP'] or image.width*image.height>25_000_000: raise ValidationError('Formato ou dimensões inválidos.')
        extension={'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}[image.format];image.verify();upload.seek(0)
        return extension
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError): raise ValidationError('Imagem inválida.')


class OutfitView(APIView):
    def post(self,request,participant_id):
        member=access(request);require(member,'outfit')
        extension=validated_image(request.FILES.get('file'));key=None
        try:
            with transaction.atomic():
                p=get_object_or_404(EventParticipant.objects.select_for_update(),pk=participant_id,event=member.event)
                ensure_writable(p)
                previous=getattr(p,'outfit_photo',None)
                previous_key=previous.storage_key if previous else None
                key=default_storage.save(f'outfits/{p.pk}/{uuid.uuid4()}{extension}',request.FILES['file'])
                outfit,_=EventOutfitPhoto.objects.update_or_create(participant=p,defaults={'storage_key':key,'captured_by':request.user})
                record(request.user,'outfit.captured',outfit,p.event,reason=str(request.data.get('reason','Ativação operacional')),previous_key=previous_key)
        except Exception:
            if key: default_storage.delete(key)
            raise
        return Response({'ok':True},status=201)


class OutfitContentView(APIView):
    def get(self, request, participant_id):
        p=current(request)
        peer=get_object_or_404(EventParticipant,pk=participant_id,event=p.event)
        if peer.pk!=p.pk:
            match=match_for(p,peer.pk)
            if not match.is_active or blocked(p,peer):
                raise PermissionDenied('Foto disponível somente após match ativo.')
        outfit=get_object_or_404(EventOutfitPhoto,participant=peer)
        if not default_storage.exists(outfit.storage_key):raise Http404
        response=FileResponse(default_storage.open(outfit.storage_key,'rb'))
        response['Cache-Control']='private, no-store'
        response['X-Content-Type-Options']='nosniff'
        return response


class ProfileInterventionView(APIView):
    def get(self,request,participant_id):
        member=access(request);require(member,'remove_photo')
        p=get_object_or_404(EventParticipant,pk=participant_id,event=member.event)
        from apps.reports.models import Report
        from apps.notifications.models import SupportThread
        return Response({'bio':p.profile.bio,
            'photos':[{'id':str(photo.pk),'url':photo.storage_key if photo.storage_key.startswith('/images/') else f'/api/event-admin/photos/{photo.pk}/content/'} for photo in ordered_photos(p) if photo.visibility=='PRE_MATCH'],
            'sources':[{'id':str(r.pk),'kind':'report','label':r.reason} for r in Report.objects.filter(reported=p)]+[{'id':str(t.pk),'kind':'support','label':t.subject} for t in SupportThread.objects.filter(participant=p)]})

    @transaction.atomic
    def post(self,request,participant_id):
        member=access(request);action=request.data.get('action')
        if action not in ['remove_photo','edit_bio']:raise ValidationError('Intervenção inválida.')
        require(member,action)
        p=get_object_or_404(EventParticipant.objects.select_for_update(),pk=participant_id,event=member.event)
        ensure_writable(p)
        reason=str(request.data.get('reason','')).strip()
        if not reason or len(reason)>4000:raise ValidationError('Informe o motivo da intervenção.')
        source=request.data.get('source');kind=request.data.get('kind')
        from apps.reports.models import Report
        from apps.notifications.models import SupportThread
        if kind=='report':get_object_or_404(Report,pk=source,reported=p)
        elif kind=='support':get_object_or_404(SupportThread,pk=source,participant=p)
        else:raise ValidationError('Vincule a intervenção a uma denúncia ou atendimento do participante.')
        if action=='remove_photo':
            obj=get_object_or_404(ParticipantPhoto,pk=request.data.get('photo'),participant=p,removed_at__isnull=True,visibility='PRE_MATCH')
            obj.removed_at=timezone.now();obj.save()
            p.is_active=False;p.registration_status='INACTIVE';p.deactivation_reason='PHOTO_REVIEW';p.save()
        else:
            bio=str(request.data.get('bio','')).strip()
            if not 50<=len(bio)<=4000:raise ValidationError('A descrição deve conter entre 50 e 4.000 caracteres.')
            obj=p.profile;previous=obj.bio;obj.bio=bio;obj.save()
        record(request.user,f'profile.{action}',obj,p.event,reason=reason,source=str(source),kind=kind,
            previous=previous if action=='edit_bio' else obj.storage_key)
        from apps.notifications.services import notify
        notify(p,'profile_intervention','A equipe atualizou seu perfil',reason,action_path='#perfil')
        return Response({'ok':True})


class ProfileFieldsView(APIView):
    @transaction.atomic
    def put(self,request):
        p=current(request);ensure_writable(p)
        EventParticipant.objects.select_for_update().get(pk=p.pk)
        values=request.data.get('values',{})
        if not isinstance(values,dict): raise ValidationError('Respostas inválidas.')
        for field_id,value in values.items():
            field=get_object_or_404(p.event.profile_fields,pk=field_id)
            if not isinstance(value,dict): raise ValidationError('Resposta inválida.')
            if field.kind=='consent' and value.get('accepted') is True:
                from apps.consent.models import ConsentRecord
                # Immutable history of each accepted version remains linked to participation.
                ConsentRecord.objects.create(user=p.user,event=p.event,purpose=f'event-field:{field.pk}',policy_version=str(field.version),granted=True)
            obj,_=ParticipantFieldValue.objects.update_or_create(participant=p,field=field,defaults={'value':{**value,'version':field.version}})
            record(request.user,'profile.field',obj,p.event)
        return Response(bootstrap(p))


class ProfileDispositionView(APIView):
    @transaction.atomic
    def post(self,request):
        p=current(request);EventParticipant.objects.select_for_update().get(pk=p.pk)
        if p.event.state not in ['CLOSED','ARCHIVED']: raise PermissionDenied('Esta escolha está disponível após o encerramento.')
        action=request.data.get('action')
        if action=='persist':
            profile,_=UserProfile.objects.get_or_create(user=request.user)
            profile.preferences={**profile.preferences,'event_profile':bootstrap(p)['profile'],
                'photos':[photo.storage_key for photo in ordered_photos(p)]}
            profile.save();record(request.user,'profile.persisted',profile,p.event)
        elif action=='delete' and request.data.get('confirmed') is True:
            p.social_deleted_at=timezone.now();p.is_active=False;p.save()
            record(request.user,'profile.social_deleted',p,p.event)
        else: raise ValidationError('Selecione e confirme a ação.')
        return Response(bootstrap(p))
