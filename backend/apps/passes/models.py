from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class PassType(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration = models.DurationField(null=True, blank=True)
    reveal_limit = models.PositiveIntegerField(null=True, blank=True)


class EventPassOffer(BaseModel):
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="pass_offers")
    pass_type = models.ForeignKey("passes.PassType", on_delete=models.PROTECT, related_name="offers")
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="BRL")


class ParticipantPass(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="passes")
    offer = models.ForeignKey("passes.EventPassOffer", on_delete=models.PROTECT, related_name="participant_passes")
    expires_at = models.DateTimeField(null=True, blank=True)


class PassUsage(BaseModel):
    participant_pass = models.ForeignKey("passes.ParticipantPass", on_delete=models.PROTECT, related_name="usages")
    revealed_participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="revelations")


class PassActivation(BaseModel):
    participant_pass = models.OneToOneField("passes.ParticipantPass", on_delete=models.PROTECT, related_name="activation")
    activated_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="+")
    activated_at = models.DateTimeField(auto_now_add=True)
