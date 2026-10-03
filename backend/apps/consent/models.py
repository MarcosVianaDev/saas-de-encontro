from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class ConsentRecord(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="consents")
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="consents", null=True, blank=True)
    purpose = models.CharField(max_length=200)
    policy_version = models.CharField(max_length=100)
    granted = models.BooleanField()
    recorded_at = models.DateTimeField(auto_now_add=True)
