from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class PassPurchase(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="purchases")
    offer = models.ForeignKey("passes.EventPassOffer", on_delete=models.PROTECT, related_name="purchases")
    reference = models.CharField(max_length=200, blank=True)


class Payment(BaseModel):
    purchase = models.ForeignKey("payments.PassPurchase", on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="BRL")
    external_reference = models.CharField(max_length=200, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
