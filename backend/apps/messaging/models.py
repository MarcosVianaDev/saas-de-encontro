from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Conversation(BaseModel):
    match = models.OneToOneField("matches.Match", on_delete=models.PROTECT, related_name="conversation")


class Message(BaseModel):
    conversation = models.ForeignKey("messaging.Conversation", on_delete=models.PROTECT, related_name="messages")
    sender = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="messages_sent")
    body = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['conversation', 'updated_at', 'id'], name='message_conversation_sync_idx'),
            models.Index(fields=['conversation'], condition=models.Q(read_at__isnull=True), name='message_unread_sync_idx'),
        ]
