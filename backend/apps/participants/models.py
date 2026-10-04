from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class EventParticipant(BaseModel):
    class Status(models.TextChoices):
        INCOMPLETE = 'INCOMPLETE', 'Cadastro incompleto'
        PENDING = 'PENDING', 'Aguardando ativação'
        ACTIVE = 'ACTIVE', 'Ativo'
        INACTIVE = 'INACTIVE', 'Desativado'

    registration_status = models.CharField(max_length=12, choices=Status.choices, default=Status.INCOMPLETE)
    activated_at = models.DateTimeField(null=True, blank=True)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    social_deleted_at = models.DateTimeField(null=True, blank=True)
    deactivation_reason = models.CharField(max_length=100, blank=True)
    presence = models.CharField(max_length=12, default='UNKNOWN', choices=[('UNKNOWN', 'Não confirmada'), ('PRESENT', 'Presente'), ('OUTSIDE', 'Temporariamente fora'), ('DISTANT', 'Fora do limite')])
    location_consent = models.BooleanField(default=False)
    location_failure_started_at = models.DateTimeField(null=True,blank=True)
    location_retry_count = models.PositiveSmallIntegerField(default=0)
    location_last_attempt_at = models.DateTimeField(null=True,blank=True)
    location_retry_exhausted_at = models.DateTimeField(null=True,blank=True)
    location_next_due_at = models.DateTimeField(null=True,blank=True)
    location_exception_until = models.DateTimeField(null=True,blank=True)
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="participants")
    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="event_participations")
    is_active = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    @property
    def operational_status(self):
        from django.utils import timezone
        from django.db.models import Q
        from apps.moderation.models import UserSuspension
        if not self.user.is_active or UserSuspension.objects.filter(user=self.user).filter(Q(ends_at__isnull=True)|Q(ends_at__gt=timezone.now())).exists():
            return 'Conta suspensa'
        if self.event.state in ['CLOSED', 'ARCHIVED']:
            return 'Evento encerrado'
        if self.active_ban:
            return 'Banido'
        if self.event_suspensions.filter(revoked_at__isnull=True).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now())).exists():
            return 'Suspenso'
        if self.is_active:
            return 'Ativo'
        return self.get_registration_status_display()

    class Meta:
        constraints = [models.UniqueConstraint(fields=('event', 'user'), name="participants_eventparticipant_unique")]

    @property
    def active_ban(self):
        ban=getattr(self,'ban',None)
        return ban if ban and ban.revoked_at is None else None


class LocationReading(BaseModel):
    participant = models.ForeignKey(EventParticipant,on_delete=models.PROTECT,related_name='location_readings')
    latitude = models.FloatField(validators=[MinValueValidator(-90),MaxValueValidator(90)])
    longitude = models.FloatField(validators=[MinValueValidator(-180),MaxValueValidator(180)])
    accuracy_m = models.FloatField(validators=[MinValueValidator(0)])
    distance_m = models.FloatField()
    measured_at = models.DateTimeField()
    speed_kmh = models.FloatField(null=True,blank=True)
    anomalous = models.BooleanField(default=False)


class LocationException(BaseModel):
    participant = models.ForeignKey(EventParticipant,on_delete=models.PROTECT,related_name='location_exceptions')
    actor = models.ForeignKey('accounts.User',on_delete=models.PROTECT,related_name='+')
    reason = models.TextField()
    expires_at = models.DateTimeField()


class LocationAnomaly(BaseModel):
    participant = models.ForeignKey(EventParticipant,on_delete=models.PROTECT,related_name='location_anomalies')
    reading = models.OneToOneField(LocationReading,on_delete=models.PROTECT,related_name='anomaly')
    criterion = models.CharField(max_length=20)
    resolution = models.CharField(max_length=20,blank=True,choices=[('DISCARDED','Anomalia descartada'),('NO_RESTRICTION','Tratado sem restrição'),('EVENT_BAN','Banimento do evento')])
    reason = models.TextField(blank=True)
    resolved_by = models.ForeignKey('accounts.User',on_delete=models.PROTECT,null=True,blank=True,related_name='+')
