from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Event(BaseModel):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="events")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)


class EventAdministrator(BaseModel):
    role = models.CharField(max_length=20, choices=[('ADMIN', 'Administrador'), ('MODERATOR', 'Moderador'), ('OPERATOR', 'Operador')], default='ADMIN')
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="administrators")
    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="event_administrations")

    class Meta:
        constraints = [models.UniqueConstraint(fields=('event', 'user'), name="events_eventadministrator_unique")]
