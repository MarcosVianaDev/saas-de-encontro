from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Match(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="matches_started")
    partner = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="matches_received")
    is_active = models.BooleanField(default=True)
    ended_at = models.DateTimeField(null=True, blank=True)
