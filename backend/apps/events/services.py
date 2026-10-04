from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.audit.services import record
from apps.notifications.models import Notification
from .models import Event, EventAdministrator
from django.core.exceptions import ValidationError as ModelValidationError


TRANSITIONS = {
    'DRAFT': ['SCHEDULED'], 'SCHEDULED': ['OPEN'], 'OPEN': ['RUNNING', 'CLOSED'],
    'RUNNING': ['PAUSED', 'CLOSED'], 'PAUSED': ['RUNNING', 'CLOSED'],
    'CLOSED': ['ARCHIVED'], 'ARCHIVED': [],
}


def managers(event):
    from django.contrib.auth import get_user_model
    return get_user_model().objects.filter(is_active=True).filter(
        Q(is_superuser=True) | Q(pk=event.responsible_id) |
        Q(event_administrations__event=event, event_administrations__role='ADMIN', event_administrations__is_active=True)).distinct()


def notify_managers(event, title, body):
    Notification.objects.bulk_create([Notification(recipient=user, event=event, title=title, body=body) for user in managers(event)])


def is_manager(user, event):
    if user and user.is_active and user.is_superuser:
        return True
    if not user:
        return False
    member = EventAdministrator.objects.filter(user=user, event=event, is_active=True).first()
    return bool(member and member.role == 'ADMIN' and not member.delegated_to_id) or EventAdministrator.objects.filter(
        event=event, is_active=True, delegated_to=user).exists()


@transaction.atomic
def configure(event,actor,data,confirmed=False):
    event=Event.objects.select_for_update().get(pk=event.pk)
    if not is_manager(actor,event):raise PermissionDenied('Seu papel não permite gerenciar o evento.')
    if event.state in ['CLOSED','ARCHIVED']:raise PermissionDenied('Evento encerrado: configurações em modo somente leitura.')
    if event.state=='SCHEDULED' and not confirmed:raise ValidationError('Confirme a alteração das configurações do evento agendado.')
    allowed={'name','description','mode','starts_at','ends_at','latitude','longitude','radius_m','tolerance_m','location_interval_minutes','settings','organization','responsible','pass_payment_instructions'}
    if set(data)-allowed:raise ValidationError('Configuração desconhecida.')
    if event.state not in ['DRAFT','SCHEDULED'] and set(data)-{'latitude','longitude','radius_m','tolerance_m','pass_payment_instructions'}:
        raise PermissionDenied('Esta configuração não pode mais ser alterada após a abertura do evento.')
    if event.state in ['RUNNING','PAUSED']:raise PermissionDenied('Esta configuração não pode mais ser alterada porque o evento já está em andamento.')
    if {'starts_at','ends_at','organization','responsible','pass_payment_instructions'}&set(data) and not actor.is_superuser:
        raise PermissionDenied('Somente a Administração Global define datas, organização e responsável.')
    previous={}
    try:
        for key,value in data.items():
            field=event._meta.get_field(key);previous[key]=str(getattr(event,field.attname))
            if field.is_relation:
                setattr(event,field.attname,field.target_field.to_python(value) if value else None)
            else:
                setattr(event,key,field.to_python(value))
            if key in ['starts_at','ends_at'] and getattr(event,key) and timezone.is_naive(getattr(event,key)):
                raise ValidationError('Informe datas com fuso horário.')
        if not isinstance(event.settings,dict):raise ValidationError('Configurações inválidas.')
        event.full_clean()
    except (ModelValidationError,ValueError,TypeError):raise ValidationError('Verifique os valores das configurações e as datas do evento.')
    event._domain_write=True;event.save()
    record(actor,'event.configuration',event,event,previous=previous,values={key:str(getattr(event,event._meta.get_field(key).attname)) for key in data})
    return event


@transaction.atomic
def transition(event, new_state, actor=None, automatic=False, reason='', now=None):
    now = now or timezone.now()
    event = Event.objects.select_for_update().get(pk=event.pk)
    if not automatic and not is_manager(actor, event):
        raise PermissionDenied('Somente a gestão responsável pode alterar o estado do evento.')
    if new_state == event.state:
        return event  # retries are idempotent, including side effects
    if new_state not in TRANSITIONS[event.state]:
        raise ValidationError('Esta transição não está disponível no estado atual.')
    previous = event.state
    if new_state == 'SCHEDULED':
        if not event.starts_at or not event.ends_at:
            raise ValidationError('Defina início e término antes de agendar.')
        event.full_clean()
    elif new_state == 'OPEN':
        if not event.starts_at or now < event.starts_at - timedelta(hours=2):
            raise ValidationError('O evento pode ser aberto a partir de duas horas antes do início.')
        event.opened_at = now
        event.opening_origin = 'automatic' if automatic else 'manual'
    elif new_state == 'RUNNING' and previous == 'OPEN':
        start = event.starts_at + (timedelta(minutes=10) if event.opening_origin == 'automatic' else timedelta())
        if now < start:
            raise ValidationError('Aguarde o horário de início do evento.')
    elif new_state == 'CLOSED':
        if not automatic and event.ends_at and now < event.ends_at and not reason.strip():
            raise ValidationError('Informe a justificativa do encerramento antecipado.')
        event.closed_at = now
    elif new_state == 'ARCHIVED':
        if not automatic or not event.closed_at or now < event.closed_at + timedelta(days=15):
            raise ValidationError('O arquivamento ocorre automaticamente quinze dias após o encerramento.')
        event.archived_at = now
    event.state = new_state
    event._domain_write = True
    event.save()
    record(actor, 'event.transition', event, event, previous=previous, state=new_state,
        automatic=automatic, reason=reason, timestamp=now.isoformat())
    title = f'O evento “{event.name}” foi {event.get_state_display().lower()}.'
    notify_managers(event, title, 'A transição foi registrada na auditoria.')
    Notification.objects.bulk_create([Notification(participant=p, event=event, title='O evento começou' if new_state=='RUNNING' else title,
        action_path='#descobrir' if new_state=='RUNNING' else '#perfil',
        body='A descoberta de participantes já está disponível.' if new_state == 'RUNNING' else 'Os dados operacionais passaram para modo somente leitura.' if new_state in ['CLOSED','ARCHIVED'] else 'Consulte as condições atuais do evento.')
        for p in event.participants.all()])
    return event


def synchronize(now=None):
    now = now or timezone.now()
    changed = 0
    for event in Event.objects.exclude(state='ARCHIVED').order_by('id'):
        # Closing always takes precedence, including a paused event.
        if event.state in ['OPEN', 'RUNNING', 'PAUSED'] and event.ends_at and now >= event.ends_at:
            transition(event, 'CLOSED', automatic=True, now=now); changed += 1
        elif event.state == 'SCHEDULED' and event.starts_at and now >= event.starts_at - timedelta(minutes=5):
            event = transition(event, 'OPEN', automatic=True, now=now); changed += 1
        if event.state == 'OPEN' and event.starts_at:
            start = event.starts_at + (timedelta(minutes=10) if event.opening_origin == 'automatic' else timedelta())
            if event.ends_at and now >= event.ends_at:
                transition(event, 'CLOSED', automatic=True, now=now); changed += 1
            elif now >= start:
                transition(event, 'RUNNING', automatic=True, now=now); changed += 1
        elif event.state == 'CLOSED' and event.closed_at and now >= event.closed_at + timedelta(days=15):
            transition(event, 'ARCHIVED', automatic=True, now=now); changed += 1
    return changed
