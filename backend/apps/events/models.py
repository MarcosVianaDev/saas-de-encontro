from django.db import models
from datetime import timedelta
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
    requested_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, null=True, blank=True, related_name='requested_events')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    radius_m = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1)])
    tolerance_m = models.PositiveIntegerField(default=1000)
    location_interval_minutes = models.PositiveIntegerField(default=15, validators=[MinValueValidator(1)])
    mode = models.CharField(max_length=10, choices=[('ONLINE', 'Online'), ('PHYSICAL', 'Presencial'), ('HYBRID', 'Híbrido')], default='PHYSICAL')
    settings = models.JSONField(default=dict, blank=True)
    pass_payment_instructions=models.TextField(blank=True)

    @property
    def auto_activate_participants(self):
        return self.mode == "ONLINE" and self.settings.get("auto_activate_participants") is True

    def clean(self):
        super().clean()
        option = self.settings.get("auto_activate_participants", False) if isinstance(self.settings, dict) else None
        if not isinstance(option, bool):
            raise ValidationError("A opção de ativação automática deve ser booleana.")
        if option and self.mode != "ONLINE":
            raise ValidationError("A ativação automática está disponível somente para eventos online.")
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError('O término deve ser posterior ao início.')
        gift = self.settings.get('initial_gift', {}) if isinstance(self.settings, dict) else {}
        if gift.get('enabled'):
            delay = gift.get('delay_minutes', 0)
            if not isinstance(delay, int) or isinstance(delay, bool) or not 0 <= delay <= 525600:
                raise ValidationError('Informe um prazo válido para o presente inicial.')
            if self.starts_at and self.ends_at and self.starts_at + timedelta(minutes=delay) >= self.ends_at:
                raise ValidationError('O horário do presente deve ser anterior ao término do evento.')
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


class ExportJob(BaseModel):
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='exports')
    requested_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='exports')
    reference = models.CharField(max_length=500, blank=True)
    modules = models.JSONField(default=list)
    state = models.CharField(max_length=12, default='PENDING', choices=[('PENDING', 'Pendente'), ('PROCESSING', 'Processando'), ('COMPLETED', 'Concluído'), ('FAILED', 'Falhou')])
    progress = models.PositiveSmallIntegerField(default=0)
    stage = models.CharField(max_length=200, default='Aguardando Celery')
    attempts = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    zip_path = models.CharField(max_length=500, blank=True)
    pdf_path = models.CharField(max_length=500, blank=True)
    zip_sha256 = models.CharField(max_length=64, blank=True)
    pdf_sha256 = models.CharField(max_length=64, blank=True)
    error = models.CharField(max_length=500, blank=True)
    manifest = models.JSONField(default=dict)
    signed_pdf_path = models.CharField(max_length=500, blank=True)
    signed_pdf_sha256 = models.CharField(max_length=64, blank=True)
    signature_reference = models.CharField(max_length=500, blank=True)
    delivery_reference = models.CharField(max_length=500, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['event'], condition=models.Q(state__in=['PENDING', 'PROCESSING']), name='event_one_active_export')]
