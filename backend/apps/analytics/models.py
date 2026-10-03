from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class EventMetric(BaseModel):
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="metrics")
    name = models.CharField(max_length=200)
    value = models.DecimalField(max_digits=20, decimal_places=4)
    measured_at = models.DateTimeField()
