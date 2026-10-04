from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Block(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="blocks_sent")
    target = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="blocks_received")

    class Meta:
        constraints = [models.UniqueConstraint(fields=('participant', 'target'), name="reports_block_unique")]


class Report(BaseModel):
    reporter = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="reports_sent", null=True, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    reported = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="reports_received")
    reason = models.TextField()
    description = models.TextField(blank=True)
    is_administrative = models.BooleanField(default=False)


class ReportEvidence(BaseModel):
    report = models.ForeignKey("reports.Report", on_delete=models.PROTECT, related_name="evidence")
    description = models.TextField(blank=True)
    storage_key = models.CharField(max_length=1024, blank=True)
