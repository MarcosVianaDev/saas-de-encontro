from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Conversation(BaseModel):
    match = models.OneToOneField("matches.Match", on_delete=models.PROTECT, related_name="conversation")


class Message(BaseModel):
    conversation = models.ForeignKey("messaging.Conversation", on_delete=models.PROTECT, related_name="messages")
    sender = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="messages_sent")
    body = models.TextField()
