from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from apps.audit.services import record
from apps.events.services import notify_managers
from .models import EventAnnouncement
from .services import notify


def deliver_sent_announcements(participant):
    for announcement in EventAnnouncement.objects.filter(
        event_id=participant.event_id, state='SENT', sent_at__isnull=False,
    ).order_by('sent_at', 'id'):
        notify(participant,'announcement',announcement.title,announcement.body,
               key=f'announcement:{announcement.pk}:{participant.pk}',action_path=announcement.url)


@transaction.atomic
def send(announcement,actor=None,automatic=False):
    from apps.events.models import Event
    event=Event.objects.select_for_update().get(pk=announcement.event_id)
    a=EventAnnouncement.objects.select_for_update().get(pk=announcement.pk)
    a.event=event
    if a.sent_at:return a
    if automatic and a.state!='SCHEDULED':return a
    if automatic and a.event.state in ['DRAFT','SCHEDULED']:return a
    if a.event.state in ['CLOSED','ARCHIVED']:
        if not automatic:raise PermissionDenied('Não é permitido enviar avisos após o encerramento.')
        a.state='CANCELLED';a.save()
        notify_managers(a.event,f'O aviso “{a.title}” não foi enviado porque o evento foi encerrado.','Não há ação de envio disponível.')
        record(None,'announcement.cancelled',a,a.event)
        return a
    if a.event.state=='PAUSED' and automatic:
        a.state='HELD';a.save()
        notify_managers(a.event,f'O aviso “{a.title}” não foi enviado porque o evento está pausado.','Você pode enviar manualmente pela área de Avisos do Evento.')
        record(None,'announcement.held',a,a.event);return a
    if a.event.state not in ['OPEN','RUNNING','PAUSED']:raise PermissionDenied('Avisos indisponíveis no estado atual do evento.')
    for p in a.event.participants.all():
        notify(p,'announcement',a.title,a.body,key=f'announcement:{a.pk}:{p.pk}',action_path=a.url)
    a.sent_at=timezone.now();a.state='SENT';a.save()
    record(actor,'announcement.sent',a,a.event,automatic=automatic)
    return a


def dispatch_due(now=None):
    now=now or timezone.now();count=0
    for a in EventAnnouncement.objects.filter(state='SCHEDULED',scheduled_at__lte=now):
        send(a,automatic=True);count+=1
    return count
