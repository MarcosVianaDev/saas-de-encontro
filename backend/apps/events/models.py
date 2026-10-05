from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel
from django.core.exceptions import ValidationError


class Event(BaseModel):
    class State(models.TextChoices):
        DRAFT = 'DRAFT', 'Rascunho'
        SCHEDULED = 'SCHEDULED', 'Agendado'
        OPEN = 'OPEN', 'Aberto'
        RUNNING = 'RUNNING', 'Em andamento'
        PAUSED = 'PAUSED', 'Pausado'
        CLOSED = 'CLOSED', 'Encerrado'
        ARCHIVED = 'ARCHIVED', 'Arquivado'

    state = models.CharField(max_length=12, choices=State.choices, default=State.DRAFT, db_index=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="events")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    opening_origin = models.CharField(max_length=10, blank=True, choices=[('manual', 'Manual'), ('automatic', 'Automática')])
    closed_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    responsible = models.ForeignKey('accounts.User', on_delete=models.PROTECT, null=True, blank=True, related_name='managed_events')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    radius_m = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1)])
    tolerance_m = models.PositiveIntegerField(default=1000)
    location_interval_minutes = models.PositiveIntegerField(default=15, validators=[MinValueValidator(1)])
    mode = models.CharField(max_length=10, choices=[('ONLINE', 'Online'), ('PHYSICAL', 'Presencial'), ('HYBRID', 'Híbrido')], default='PHYSICAL')
    settings = models.JSONField(default=dict, blank=True)
    pass_payment_instructions=models.TextField(blank=True)

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError('O término deve ser posterior ao início.')
        if self.mode != 'ONLINE' and (self.latitude is None or self.longitude is None):
            raise ValidationError('Informe o ponto de referência do evento presencial.')

    def save(self, *args, **kwargs):
        if not self._state.adding and not getattr(self, '_domain_write', False):
            previous = type(self).objects.get(pk=self.pk)
            if previous.state != self.state:
                raise ValidationError('Use o serviço de transição do evento.')
        super().save(*args, **kwargs)


class EventAdministrator(BaseModel):
    is_active = models.BooleanField(default=True)
    permissions = models.JSONField(default=list, blank=True)
    delegated_to = models.ForeignKey('accounts.User', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    role = models.CharField(max_length=20, choices=[('ADMIN', 'Administrador'), ('MODERATOR', 'Moderador'), ('OPERATOR', 'Operador')], default='ADMIN')
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="administrators")
    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="event_administrations")

    class Meta:
        constraints = [models.UniqueConstraint(fields=('event', 'user'), name="events_eventadministrator_unique")]
