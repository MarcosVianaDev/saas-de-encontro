from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Match(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="matches_started")
    partner = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="matches_received")
    is_active = models.BooleanField(default=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    ended_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, null=True, blank=True, related_name="ended_matches")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["participant", "partner"], name="matches_pair_unique"),
            models.CheckConstraint(condition=models.Q(participant__lt=models.F("partner")), name="matches_pair_ordered"),
        ]
