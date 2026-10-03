from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class ProfileDiscovery(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="discoveries")
    candidate = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="discovered_by")
    presented_at = models.DateTimeField(auto_now_add=True)
