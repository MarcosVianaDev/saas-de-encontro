from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class EventParticipant(BaseModel):
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="participants")
    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="event_participations")
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('event', 'user'), name="participants_eventparticipant_unique")]
