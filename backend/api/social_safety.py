from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.participants.models import EventParticipant
from apps.reports.models import Block, Report, ReportEvidence
from apps.moderation.models import ModerationCase
from apps.profiles.models import ParticipantPhoto
from apps.messaging.models import Message
from apps.audit.services import record
from apps.notifications.models import Notification
from apps.events.services import managers
from apps.notifications.services import notify
from .services import current, bootstrap, ensure_writable, blocked, match_for

REASONS=['Ofensa, ameaça ou assédio','Importunação ou comportamento sexual indesejado','Nudez ou conteúdo sexual explícito',
    'Racismo ou discriminação','Discurso de ódio','Violência ou ameaça','Fraude ou golpe','Uso indevido de imagem ou identidade','Conteúdo ou comportamento possivelmente ilegal','Outro']


def thresholds(p):
    count=p.reports_received.filter(is_administrative=False,is_unfounded=False).count()
    if count>=10:
        for m in p.event.administrators.filter(is_active=True,role__in=['ADMIN','MODERATOR']).select_related('user'):
            Notification.objects.get_or_create(dedupe_key=f'reports10:{p.pk}:{m.user_id}',defaults={'recipient':m.user,'event':p.event,
                'kind':'reports10','title':f'Participante {p.profile.first_name} recebeu dez denúncias relevantes','body':'Clique para revisar o participante.',
                'action_path':f'#admin-participants?participant={p.pk}'})
    if count>=20:
        p.is_active=False;p.registration_status='INACTIVE';p.deactivation_reason='REPORT_REVIEW';p.save()
        notify(p,'profile_review','Seu perfil está temporariamente em análise','Algumas funções foram desativadas enquanto a equipe responsável analisa uma ocorrência.',key=f'reports20:participant:{p.pk}',action_path='#mensagens')
        for user in managers(p.event).filter(is_superuser=True):
            Notification.objects.get_or_create(dedupe_key=f'reports20:{p.pk}:{user.pk}',defaults={'recipient':user,'event':p.event,'title':'Perfil desativado após vinte denúncias relevantes','body':p.event.name,'kind':'reports20'})


class BlockView(APIView):
    @transaction.atomic
    def post(self,request,peer_id):
        p=current(request);ensure_writable(p)
        target=get_object_or_404(EventParticipant,pk=peer_id,event=p.event)
        if p.pk==target.pk: raise ValidationError('Selecione outro participante.')
        if request.data.get('confirmed') is not True: raise ValidationError('Confirme o bloqueio neste evento.')
        list(EventParticipant.objects.select_for_update().filter(pk__in=[p.pk,target.pk]).order_by('id'))
        block,created=Block.objects.get_or_create(participant=p,target=target,defaults={'reason':str(request.data.get('reason',''))[:4000]})
        if created:record(request.user,'participant.blocked',block,p.event)
        return Response(bootstrap(p))


class ReportView(APIView):
    def get(self,request,peer_id=None):
        p=current(request)
        if peer_id is None:return Response({'reasons':REASONS})
        target=get_object_or_404(EventParticipant,pk=peer_id,event=p.event)
        from apps.matches.models import Match
        matches=Match.objects.filter(Q(participant=p,partner=target)|Q(participant=target,partner=p))
        matched=matches.filter(is_active=True).exists() and not blocked(p,target)
        photos=target.photos.filter(removed_at__isnull=True)
        if blocked(p,target) or target.social_deleted_at:photos=photos.none()
        if not matched:photos=photos.filter(visibility='PRE_MATCH')
        from .services import photo_url
        messages=Message.objects.filter(conversation__match__in=matches).order_by('created_at')
        return Response({'reasons':REASONS,'photos':[{'id':str(photo.pk),'url':photo_url(photo)} for photo in photos],
            'messages':[{'id':str(m.pk),'body':m.body} for m in messages]})

    @transaction.atomic
    def post(self,request,peer_id):
        p=current(request)
        target=get_object_or_404(EventParticipant.objects.select_for_update(),pk=peer_id,event=p.event)
        if p.pk==target.pk:raise ValidationError('Não é permitido denunciar a si mesmo.')
        description=str(request.data.get('description','')).strip()
        reasons=request.data.get('reasons',[])
        if not description or len(description)>4000 or not isinstance(reasons,list) or not reasons or set(reasons)-set(REASONS):
            raise ValidationError('Selecione os motivos e conte o que aconteceu (até 4.000 caracteres).')
        report=Report.objects.create(reporter=p,reported=target,reason=', '.join(reasons),reasons=reasons,description=description)
        evidence=request.data.get('evidence',{})
        if not isinstance(evidence,dict):raise ValidationError('Evidência inválida.')
        if evidence.get('photo'):
            photo=get_object_or_404(ParticipantPhoto,pk=evidence['photo'],participant=target)
            if photo.visibility=='POST_MATCH':
                match=match_for(p,peer_id)
                if not match.is_active or blocked(p,target):raise PermissionDenied('Esta foto não está disponível.')
            ReportEvidence.objects.create(report=report,description='Foto relacionada',storage_key=photo.storage_key,snapshot={'photo':str(photo.pk),'removed':bool(photo.removed_at)})
        if evidence.get('message'):
            match=match_for(p,peer_id)
            message=get_object_or_404(Message,pk=evidence['message'],conversation=match.conversation)
            ReportEvidence.objects.create(report=report,description='Mensagem relacionada',snapshot={'message':str(message.pk),'body':message.body,'sender':str(message.sender_id)})
        if evidence.get('context') or evidence.get('photoChanged'):
            ReportEvidence.objects.create(report=report,description=str(evidence.get('context','Foto alterada ou removida'))[:4000],snapshot={'photoChanged':bool(evidence.get('photoChanged'))})
        case=ModerationCase.objects.create(report=report,priority=2 if target.reports_received.filter(is_unfounded=False,is_administrative=False).count()>=10 else 1)
        record(request.user,'case.created',case,p.event)
        thresholds(target)
        return Response({'ok':True},status=201)
