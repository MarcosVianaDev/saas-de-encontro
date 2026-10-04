from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.events.models import Event, EventAdministrator
from apps.events.services import transition
from apps.organizations.models import Organization
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


class GlobalView(APIView):
    def get(self,request):
        authorize(request)
        return Response({'navigation':'global', 'staff':request.user.is_staff,
            'metrics':{**{s:Event.objects.filter(state=s).count() for s in ['RUNNING','SCHEDULED','PAUSED']},
                'clients':Organization.objects.filter(is_active=True).count(),
                'critical':ModerationCase.objects.filter(priority=2,closed_at__isnull=True).count(),
                'pending':ModerationCase.objects.filter(closed_at__isnull=True).count()},
            'clients':[{'id':str(o.pk),'name':o.name,'contact':o.contact_name,'email':o.contact_email,'active':o.is_active,'draft':o.onboarding_draft} for o in Organization.objects.order_by('-created_at')],
            'events':[{'id':str(e.pk),'name':e.name,'state':e.state,'status':e.get_state_display(),'organization':e.organization.name} for e in Event.objects.select_related('organization').order_by('-created_at')],
            'safety':[{'id':str(p.pk),'user':str(p.user_id),'email':p.user.email,'recurring':p.recurring_reported,
                'reports':Report.objects.filter(reported__user=p.user,is_unfounded=False,is_administrative=False).count(),
                'events':[{'id':str(ep.event_id),'name':ep.event.name} for ep in p.user.event_participations.select_related('event')]} for p in UserProfile.objects.filter(Q(recurring_reported=True)|Q(user__event_participations__reports_received__is_unfounded=False,user__event_participations__reports_received__is_administrative=False)).select_related('user').distinct()],
            'activity':[{'id':str(a.pk),'action':a.action,'created':a.created_at} for a in AuditLog.objects.order_by('-created_at')[:20]],
            'alerts':[{'id':str(n.pk),'title':n.title,'body':n.body} for n in Notification.objects.filter(recipient=request.user,read_at__isnull=True).order_by('-created_at')[:20]]})

    @transaction.atomic
    def post(self,request):
        authorize(request)
        d = request.data
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
