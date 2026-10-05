from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.dateparse import parse_datetime
from django.core.validators import URLValidator
from rest_framework.exceptions import PermissionDenied,ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.notifications.models import Notification,EventAnnouncement
from apps.notifications.announcements import send
from apps.events.permissions import require
from apps.audit.services import record
from .event_admin import access


def notification_participant(notification):
    p = notification.participant
    if p is None or not notification.dedupe_key:
        return None
    from apps.matches.models import Match
    from apps.interactions.models import Interaction
    from apps.passes.services import revealed_ids
    from .services import visible_participants
    parts = notification.dedupe_key.split(':')
    if len(parts) < 2:
        return None
    try:
        if notification.kind == 'like' and parts[0] == 'like':
            like = Interaction.objects.filter(pk=parts[1], target=p, decision='LIKE').first()
            if not like:
                return None
            peer = like.participant_id
            matched = Match.objects.filter(is_active=True).filter(
                Q(participant=p, partner_id=peer) | Q(partner=p, participant_id=peer),
            ).exists()
            if str(peer) not in revealed_ids(p) and not matched:
                return None
        elif notification.kind == 'match' and parts[0] == 'match':
            match = Match.objects.filter(pk=parts[1], is_active=True).filter(Q(participant=p) | Q(partner=p)).first()
            if not match:
                return None
            peer = match.partner_id if match.participant_id == p.pk else match.participant_id
        else:
            return None
    except (ValueError, DjangoValidationError):
        return None
    return str(peer) if visible_participants(p).filter(pk=peer).exists() else None


class NotificationView(APIView):
    def query(self,request):
        q=Notification.objects.filter(Q(recipient=request.user)|Q(participant__user=request.user))
        if request.session.get('event_id'):q=q.filter(Q(event_id=request.session['event_id'])|Q(event__isnull=True,participant__event_id=request.session['event_id']))
        return q.select_related('participant__event').order_by('-created_at')

    def get(self,request):
        q=self.query(request)
        return Response({'unread':q.filter(read_at__isnull=True).count(),'items':[{'id':str(n.pk),'title':n.title,'body':n.body,'kind':n.kind,'read':bool(n.read_at),'created':n.created_at,'action':n.action_path,'participant':notification_participant(n)} for n in q[:100]]})

    def post(self,request):
        obj=get_object_or_404(self.query(request),pk=request.data.get('id'))
        if not obj.read_at:obj.read_at=timezone.now();obj.save(update_fields=['read_at','updated_at'])
        return Response({'ok':True})


def announcement_payload(a):
    return {'id':str(a.pk),'title':a.title,'body':a.body,'url':a.url,'state':a.state,'scheduled':a.scheduled_at,'sent':a.sent_at}


class AnnouncementView(APIView):
    def get(self,request):
        member=access(request);require(member,'announcements')
        return Response([announcement_payload(a) for a in member.event.announcements.order_by('-created_at')])

    @transaction.atomic
    def post(self,request):
        member=access(request);require(member,'announcements')
        if member.event.state not in ['OPEN','RUNNING','PAUSED']:raise PermissionDenied('Avisos podem ser criados ou editados em Aberto, Em andamento e Pausado.')
        d=request.data;action=d.get('action','draft')
        a=get_object_or_404(EventAnnouncement.objects.select_for_update(),pk=d['id'],event=member.event) if d.get('id') else EventAnnouncement(event=member.event,author=request.user)
        if a.sent_at:raise PermissionDenied('Avisos enviados não podem ser editados.')
        a.title=str(d.get('title',a.title)).strip();a.body=str(d.get('body',a.body)).strip();a.url=str(d.get('url',a.url)).strip()
        if not a.title or len(a.title)>200 or not a.body or len(a.body)>10000:raise ValidationError('Informe título e mensagem válidos.')
        if a.url:URLValidator(schemes=['http','https'])(a.url)
        if action=='schedule':
            scheduled=parse_datetime(str(d.get('scheduled','')))
            if not scheduled or timezone.is_naive(scheduled) or scheduled<=timezone.now():raise ValidationError('Informe um horário futuro com fuso horário.')
            if not member.event.ends_at or scheduled>=member.event.ends_at:raise ValidationError('Não é permitido agendar após o encerramento previsto.')
            if scheduled>=member.event.ends_at-timedelta(minutes=30) and d.get('confirmed') is not True:raise ValidationError('Este aviso está próximo ao encerramento. Confirme explicitamente o agendamento.')
            a.scheduled_at=scheduled;a.state='SCHEDULED'
        elif action=='draft':a.state='DRAFT';a.scheduled_at=None
        elif action!='send':raise ValidationError('Ação inválida.')
        a.full_clean();a.save()
        if action=='send':
            if d.get('confirmed') is not True:raise ValidationError('Confirme o envio para os participantes.')
            a=send(a,actor=request.user)
        else:record(request.user,'announcement.'+action,a,member.event)
        return Response(announcement_payload(a))
