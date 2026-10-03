from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class DataRetentionRecord(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="retention_records")
    category = models.CharField(max_length=200)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)


class LegalHold(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="legal_holds")
    reason = models.TextField()
    released_at = models.DateTimeField(null=True, blank=True)


class PrivacyRequest(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="privacy_requests")
    description = models.TextField()
    completed_at = models.DateTimeField(null=True, blank=True)
