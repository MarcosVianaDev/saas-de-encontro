"""Small invalidations only. Data and writes remain behind the HTTP permissions."""
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

logger = logging.getLogger(__name__)


def account_group(context, user_id, event_id=None):
    return '.'.join(['rt', context, str(event_id or 'global'), str(user_id)])


def event_group(event_id):
    return f'rt.event.{event_id}'


def publish(groups, topics, using=None):
    groups, topics = tuple(set(groups)), sorted(set(topics))
    if not groups:
        return

    def committed():
        async def send():
            layer = get_channel_layer()
            for group in groups:
                await layer.group_send(group, {'type': 'realtime.changed', 'topics': topics})
        try:
            async_to_sync(send)()
        except Exception:
            # Redis downtime must not turn a committed message into an HTTP error.
            # Reconnection and the HTTP fallback recover the persisted data.
            logger.exception('Could not publish realtime invalidation')

    transaction.on_commit(committed, using=using)


def participants_changed(identifiers, topics, using=None):
    from apps.participants.models import EventParticipant
    rows = EventParticipant.objects.using(using).filter(pk__in=identifiers).values_list('user_id', 'event_id')
    publish([account_group('participant', user, event) for user, event in rows], topics, using)


def notifications_changed(notifications, using=None):
    from apps.participants.models import EventParticipant
    participants = {item.participant_id for item in notifications if item.participant_id and not item.recipient_id}
    rows = EventParticipant.objects.using(using).filter(pk__in=participants).values_list('user_id', 'event_id') if participants else []
    groups = {account_group('participant', user, event) for user, event in rows}
    for item in notifications:
        if item.recipient_id and not item.participant_id:
            groups.add(account_group('global', item.recipient_id))
            if item.event_id:
                groups.add(account_group('administration', item.recipient_id, item.event_id))
    publish(groups, ['notifications'], using)
