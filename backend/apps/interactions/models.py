from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Interaction(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="interactions_sent")
    target = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="interactions_received")
    decision = models.CharField(max_length=4, choices=[("LIKE", "Like"), ("PASS", "Pass")])

    class Meta:
        constraints = [models.UniqueConstraint(fields=('participant', 'target'), name="interactions_interaction_unique")]


class InteractionHistory(BaseModel):
    interaction = models.ForeignKey("interactions.Interaction", on_delete=models.PROTECT, related_name="history")
    decision = models.CharField(max_length=4, choices=[("LIKE", "Like"), ("PASS", "Pass")])
