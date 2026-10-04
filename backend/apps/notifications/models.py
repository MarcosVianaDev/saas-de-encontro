from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Notification(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="notifications", null=True, blank=True)
    recipient = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='administrative_notifications', null=True, blank=True)
    event = models.ForeignKey('events.Event', on_delete=models.PROTECT, related_name='administrative_notifications', null=True, blank=True)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
