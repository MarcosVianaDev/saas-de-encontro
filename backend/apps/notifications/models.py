from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Notification(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="notifications")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
