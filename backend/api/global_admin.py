from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from apps.events.models import Event, EventAdministrator
from apps.events.services import transition
from apps.organizations.models import Organization, OrganizationMember
from apps.audit.models import AuditLog
from apps.audit.services import record
from apps.moderation.models import ModerationCase
from apps.notifications.models import Notification
from apps.accounts.models import UserProfile
from apps.participants.models import EventParticipant
from apps.reports.models import Report
from django.db.models import Q


def authorize(request):
    if not request.user.is_active or not request.user.is_superuser:
        raise PermissionDenied('Acesso exclusivo da Administração Global.')


class ClientContactSerializer(serializers.Serializer):
    contact = serializers.CharField(max_length=200)
    email = serializers.EmailField(max_length=254)
    phone = serializers.CharField(max_length=50)


class ClientDetailsSerializer(ClientContactSerializer):
    organization = serializers.CharField(max_length=200, required=False, allow_blank=True)
    description = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    contact_role = serializers.CharField(max_length=200, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=4000, required=False, allow_blank=True)


class NewEventSerializer(serializers.Serializer):
    location_interval_minutes = serializers.IntegerField(min_value=1, default=15)
    mode = serializers.ChoiceField(choices=["ONLINE", "PHYSICAL", "HYBRID"], default="PHYSICAL")
    auto_activate_participants = serializers.BooleanField(default=False)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True, min_value=-90, max_value=90)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True, min_value=-180, max_value=180)
    client = serializers.UUIDField()
    event = serializers.CharField(max_length=200)
    starts = serializers.DateTimeField()
    ends = serializers.DateTimeField()
    responsible = serializers.EmailField()

    def validate(self, data):
        if data['ends'] <= data['starts']:
            raise serializers.ValidationError('O término deve ser posterior ao início.')
        return data


def access_user_payload(user):
    return {'id': str(user.pk), 'email': user.email, 'firstName': user.first_name,
            'lastName': user.last_name, 'passwordConfigured': user.has_usable_password()}


def client_access_user(org):
    user_id = org.onboarding_draft.get('access_user_id')
    member = next((member for member in org.members.all()
                   if str(member.user_id) == user_id), None)
    return access_user_payload(member.user) if member else None


def create_client_account(values):
    User = get_user_model()
    email = values['email'].lower()
    words = values['contact'].split()
    if len(email) > User._meta.get_field('username').max_length:
        raise ValidationError({'email': 'O e-mail excede o tamanho permitido para o login.'})
    if len(words[0]) > 150 or len(words[-1]) > 150:
        raise ValidationError({'contact': 'A primeira e a última palavra do nome devem ter até 150 caracteres.'})
    if User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
        raise ValidationError({'email': 'Já existe uma conta com este e-mail. Informe um e-mail ainda não cadastrado.'})
    try:
        with transaction.atomic():
            user = User.objects.create_user(username=email, email=email,
                first_name=words[0], last_name=words[-1], is_staff=False, is_superuser=False)
            UserProfile.objects.create(user=user)
    except IntegrityError:
        raise ValidationError({'email': 'Já existe uma conta com este e-mail.'})
    values['email'] = email
    return user


def save_client(request, action):
    creating = action == 'create_client'
    serializer = (ClientContactSerializer if creating else ClientDetailsSerializer)(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    user = create_client_account(values) if creating else None
    if creating:
        org = Organization(name=values['contact'])
    else:
        identifier = serializers.UUIDField().run_validation(request.data.get('id'))
        org = get_object_or_404(Organization.objects.select_for_update(), pk=identifier)
    draft = dict(org.onboarding_draft)
    draft.update(values)
    if user:
        draft['access_user_id'] = str(user.pk)
    org.contact_name = values['contact']
    org.contact_email = values['email']
    org.contact_phone = values['phone']
    if 'organization' in values:
        org.name = values['organization'] or org.contact_name
    elif creating or not draft.get('organization') and org.name == org.onboarding_draft.get('contact'):
        org.name = org.contact_name
    if 'description' in values:
        org.description = values['description']
    org.onboarding_draft = draft
    org.is_active = True
    org.full_clean()
    org.save()
    if user:
        OrganizationMember.objects.create(organization=org, user=user)
        record(request.user, 'account.created', user, client=str(org.pk))
    record(request.user, 'client.created' if creating else 'client.updated', org)
    return Response({'id': str(org.pk), 'ok': True, 'accessUser': access_user_payload(user) if user else client_access_user(org)}, status=201 if creating else 200)


def create_event(request):
    serializer = NewEventSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    values = serializer.validated_data
    org = get_object_or_404(Organization.objects.select_for_update(), pk=values['client'], is_active=True)
    owners = get_user_model().objects.filter(email__iexact=values['responsible'], is_active=True)
    if owners.count() != 1:
        raise ValidationError({'responsible': 'Informe o e-mail de uma conta de acesso ativa e única.'})
    owner = owners.get()
    event = Event(organization=org, name=values['event'], starts_at=values['starts'], ends_at=values['ends'], responsible=owner, mode=values['mode'], latitude=values.get('latitude'), longitude=values.get('longitude'), location_interval_minutes=values['location_interval_minutes'], settings={'auto_activate_participants': values['auto_activate_participants']})
    try:
        event.full_clean()
    except ModelValidationError as error:
        raise ValidationError(error.message_dict)
    event.save()
    EventAdministrator.objects.create(event=event, user=owner, role='ADMIN')
    transition(event, 'SCHEDULED', actor=request.user)
    record(request.user, 'event.created', event, event)
    return Response({'id': str(event.pk), 'client': str(org.pk), 'ok': True}, status=201)


class GlobalView(APIView):
    def get(self,request):
        authorize(request)
        return Response({'navigation':'global', 'staff':request.user.is_staff,
            'metrics':{**{s:Event.objects.filter(state=s).count() for s in ['RUNNING','SCHEDULED','PAUSED']},
                'clients':Organization.objects.filter(is_active=True).count(),
                'critical':ModerationCase.objects.filter(priority=2,closed_at__isnull=True).count(),
                'pending':ModerationCase.objects.filter(closed_at__isnull=True).count()},
            'clients':[{'id':str(o.pk),'name':o.name,'contact':o.contact_name,'email':o.contact_email,'phone':o.contact_phone,'description':o.description,'active':o.is_active,'draft':o.onboarding_draft,'accessUser':client_access_user(o)} for o in Organization.objects.prefetch_related('members__user').order_by('-created_at')],
            'events':[{'id':str(e.pk),'name':e.name,'state':e.state,'status':e.get_state_display(),'organization':e.organization.name,'organizationId':str(e.organization_id)} for e in Event.objects.select_related('organization').order_by('-created_at')],
            'safety':[{'id':str(p.pk),'user':str(p.user_id),'email':p.user.email,'recurring':p.recurring_reported,
                'reports':Report.objects.filter(reported__user=p.user,is_unfounded=False,is_administrative=False).count(),
                'events':[{'id':str(ep.event_id),'name':ep.event.name} for ep in p.user.event_participations.select_related('event')]} for p in UserProfile.objects.filter(Q(recurring_reported=True)|Q(user__event_participations__reports_received__is_unfounded=False,user__event_participations__reports_received__is_administrative=False)).select_related('user').distinct()],
            'activity':[{'id':str(a.pk),'action':a.action,'created':a.created_at} for a in AuditLog.objects.order_by('-created_at')[:20]],
            'alerts':[{'id':str(n.pk),'title':n.title,'body':n.body} for n in Notification.objects.filter(recipient=request.user,read_at__isnull=True).order_by('-created_at')[:20]]})

    @transaction.atomic
    def post(self,request):
        authorize(request)
        d = request.data
        if d.get('action') in ['create_client', 'update_client']:
            return save_client(request, d['action'])
        if d.get('action') == 'create_event':
            return create_event(request)
        if d.get('action') in ['recurrence','inform_event']:
            profile=get_object_or_404(UserProfile.objects.select_for_update(),pk=d.get('profile'))
            reason=str(d.get('reason','')).strip()
            if not reason or len(reason)>4000 or d.get('confirmed') is not True:raise ValidationError('Informe o motivo e confirme a decisão.')
            if d['action']=='recurrence':
                profile.recurring_reported=d.get('marked') is True;profile.save()
                record(request.user,'safety.recurrence',profile,reason=reason,marked=profile.recurring_reported)
            else:
                p=get_object_or_404(EventParticipant,user=profile.user,event_id=d.get('event'))
                from apps.events.services import notify_managers
                notify_managers(p.event,'Acompanhamento de segurança comunicado pela gestão global',reason)
                record(request.user,'safety.informed_event',profile,p.event,reason=reason)
            return Response({'ok':True})
        org = get_object_or_404(Organization.objects.select_for_update(),pk=d['id']) if d.get('id') else Organization.objects.create(name='Cliente em configuração',is_active=False)
        draft = dict(org.onboarding_draft)
        draft.update({k:v for k,v in d.items() if k not in ['id','activate']})
        org.onboarding_draft = draft
        org.name = str(draft.get('organization','')).strip() or org.name
        org.contact_name = str(draft.get('contact','')).strip()
        org.contact_email = str(draft.get('email','')).strip()
        org.contact_phone = str(draft.get('phone','')).strip()
        if d.get('activate'):
            if org.is_active: return Response({'id':str(org.pk),'ok':True})
            start = parse_datetime(str(draft.get('starts','')))
            end = parse_datetime(str(draft.get('ends','')))
            if not org.contact_name or not org.contact_email or not draft.get('organization') or not draft.get('event') or not start or not end or timezone.is_naive(start) or timezone.is_naive(end) or end <= start:
                raise ValidationError('Preencha contato, organização, evento e datas válidas.')
            owner = get_object_or_404(get_user_model(),email=draft.get('responsible'),is_active=True)
            event = Event(organization=org,name=draft['event'],starts_at=start,ends_at=end,responsible=owner)
            event.full_clean(); event.save()
            EventAdministrator.objects.create(event=event,user=owner,role='ADMIN')
            transition(event,'SCHEDULED',actor=request.user)
            org.is_active = True
            draft['event_id'] = str(event.pk)
        org.full_clean(); org.save()
        record(request.user,'client.activated' if d.get('activate') else 'client.draft',org)
        return Response({'id':str(org.pk),'ok':True})
