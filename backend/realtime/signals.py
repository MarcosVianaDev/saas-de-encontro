from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from apps.events.models import Event, EventAdministrator
from apps.matches.models import Match
from apps.messaging.models import Conversation, Message
from apps.notifications.models import Notification
from apps.participants.models import EventParticipant
from apps.reports.models import Block
from .publishing import account_group, event_group, notifications_changed, participants_changed, publish


@receiver(post_save, sender=Notification)
def notice_saved(sender, instance, using, raw=False, **kwargs):
    if not raw:
        notifications_changed([instance], using)


@receiver(post_save, sender=Message)
@receiver(post_save, sender=Conversation)
def conversation_saved(sender, instance, using, raw=False, **kwargs):
    if raw:
        return
    match = instance.conversation.match if sender is Message else instance.match
    participants_changed([match.participant_id, match.partner_id], ['messages'], using)


@receiver(post_save, sender=Match)
def match_saved(sender, instance, using, raw=False, **kwargs):
    if not raw:
        participants_changed([instance.participant_id, instance.partner_id], ['messages'], using)


@receiver(post_save, sender=Block)
@receiver(post_delete, sender=Block)
def block_changed(sender, instance, using, raw=False, **kwargs):
    if not raw:
        participants_changed([instance.participant_id, instance.target_id], ['messages', 'status'], using)


@receiver(post_save, sender=Event)
def event_saved(sender, instance, using, raw=False, **kwargs):
    if not raw:
        publish([event_group(instance.pk)], ['status'], using)


@receiver(post_save, sender=EventParticipant)
def participant_saved(sender, instance, using, raw=False, **kwargs):
    if not raw:
        publish([account_group('participant', instance.user_id, instance.event_id)], ['status'], using)


@receiver(post_save, sender=EventAdministrator)
@receiver(post_delete, sender=EventAdministrator)
def membership_changed(sender, instance, using, raw=False, **kwargs):
    if not raw:
        publish([account_group('administration', instance.user_id, instance.event_id)], ['status'], using)
