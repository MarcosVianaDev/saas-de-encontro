from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import DateTimeField, ExpressionWrapper, F, IntegerField, Q, Value
from django.db.models.functions import Cast, Coalesce
from django.utils import timezone
from rest_framework import serializers

from apps.audit.services import record
from apps.notifications.services import notify
from apps.participants.models import EventParticipant
from .models import EventPassOffer, ParticipantPass, PassActivation, PassType


class InitialGiftSerializer(serializers.Serializer):
    enabled = serializers.BooleanField(default=False)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    delay_minutes = serializers.IntegerField(min_value=0, max_value=525600, default=0)
    duration_minutes = serializers.IntegerField(min_value=0, max_value=525600, default=0)
    reveal_limit = serializers.IntegerField(min_value=0, max_value=1000000, default=0)

    def validate(self, values):
        if values['enabled']:
            if not values.get('name'):
                raise serializers.ValidationError('Informe o nome do passe de presente.')
            if bool(values['duration_minutes']) == bool(values['reveal_limit']):
                raise serializers.ValidationError('Defina a duração ou a quantidade de revelações do passe.')
        return values


def configure_initial_gift(event, values, actor):
    if not values or not values['enabled']:
        return
    kind = PassType.objects.create(name=values['name'],
        duration=timedelta(minutes=values['duration_minutes']) if values['duration_minutes'] else None,
        reveal_limit=values['reveal_limit'] or None)
    offer = EventPassOffer.objects.create(event=event, pass_type=kind, price=0)
    event.settings = {**event.settings, 'initial_gift': {
        'enabled': True, 'offer_id': str(offer.pk), 'delay_minutes': values['delay_minutes'],
    }}
    event.save(update_fields=['settings', 'updated_at'])
    record(actor, 'pass.initial_gift_configured', offer, event, delay_minutes=values['delay_minutes'])


@transaction.atomic
def grant_initial_gift(participant, now=None):
    p = EventParticipant.objects.select_for_update().select_related('event', 'user').get(pk=participant.pk)
    now = now or timezone.now()
    config = p.event.settings.get('initial_gift', {})
    if not config.get('enabled') or not p.is_active or not p.activated_at or not p.user.is_active:
        return False
    if p.event.state not in ['OPEN', 'RUNNING', 'PAUSED'] or p.active_ban:
        return False
    if p.event.ends_at and now >= p.event.ends_at:
        return False
    delay = config.get('delay_minutes', 0)
    if delay and (p.event.state != 'RUNNING' or now < p.event.starts_at + timedelta(minutes=delay)):
        return False
    if p.passes.filter(origin='INITIAL_GIFT').exists():
        return False
    offer = EventPassOffer.objects.select_related('pass_type').get(pk=config['offer_id'], event=p.event)
    gift = ParticipantPass.objects.create(participant=p, offer=offer, offer_name=offer.pass_type.name,
        granted_by=p.event.responsible, origin='INITIAL_GIFT', sale_amount=0,
        reveal_limit=offer.pass_type.reveal_limit,
        expires_at=now + offer.pass_type.duration if offer.pass_type.duration else None)
    PassActivation.objects.create(participant_pass=gift, activated_by=p.event.responsible)
    record(None, 'pass.initial_gift_granted', gift, p.event, participant=str(p.pk))
    notify(p, 'pass_activated', 'Seu presente inicial foi ativado',
        f'O passe {offer.pass_type.name} foi concedido e ativado automaticamente. Aproveite seu presente!',
        key=f'initial-gift:{p.pk}', action_path='#participantes')
    from .services import reveal_available
    reveal_available(p)
    return True


def due_initial_gift_participants(now=None, *, after=None):
    now = now or timezone.now()
    participants = EventParticipant.objects.filter(is_active=True, activated_at__isnull=False,
        user__is_active=True, event__state='RUNNING', event__settings__initial_gift__enabled=True,
    ).exclude(passes__origin='INITIAL_GIFT').filter(
        Q(event__ends_at__isnull=True) | Q(event__ends_at__gt=now),
    ).alias(
        gift_delay=Coalesce(Cast('event__settings__initial_gift__delay_minutes', IntegerField()), Value(0)),
    ).alias(gift_due_at=ExpressionWrapper(
        F('event__starts_at') + F('gift_delay') * Value(timedelta(minutes=1)),
        output_field=DateTimeField(),
    )).filter(Q(gift_delay=0) | Q(gift_due_at__lte=now))
    if after:
        participants = participants.filter(pk__gt=after)
    return participants.order_by('pk')


def grant_due_initial_gifts(now=None):
    """Synchronous maintenance helper: never grant more than one small batch."""
    now = now or timezone.now()
    participants = due_initial_gift_participants(now)[:settings.INITIAL_GIFT_BATCH_SIZE]
    return sum(grant_initial_gift(p, now) for p in participants)
