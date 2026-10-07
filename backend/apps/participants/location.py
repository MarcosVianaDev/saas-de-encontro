import math
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.audit.services import record
from apps.events.services import notify_managers
from apps.notifications.services import notify
from .models import EventParticipant,LocationReading,LocationAnomaly,LocationException


def distance(lat1,lon1,lat2,lon2):
    a,b=map(math.radians,[float(lat1),float(lat2)])
    delta_lat,delta_lon=map(math.radians,[float(lat2)-float(lat1),float(lon2)-float(lon1)])
    value=math.sin(delta_lat/2)**2+math.cos(a)*math.cos(b)*math.sin(delta_lon/2)**2
    return 6371000*2*math.asin(math.sqrt(min(1,value)))


@transaction.atomic
def reading(p,data,now=None):
    now=now or timezone.now();p=EventParticipant.objects.select_for_update().select_related('event').get(pk=p.pk)
    if p.event.mode == 'ONLINE':
        return p
    try:
        lat=float(data['latitude']);lon=float(data['longitude']);accuracy=float(data.get('accuracy',0))
        if not all(map(math.isfinite,[lat,lon,accuracy])) or not -90<=lat<=90 or not -180<=lon<=180 or accuracy<0:raise ValueError()
    except (KeyError,ValueError,TypeError):raise ValidationError('Localização inválida. Tente novamente.')
    if p.event.latitude is None or p.event.longitude is None:raise ValidationError('A equipe precisa configurar o ponto de referência do evento.')
    d=distance(lat,lon,p.event.latitude,p.event.longitude)
    previous=p.location_readings.order_by('-measured_at','-id').first()
    speed=None
    if previous:
        seconds=(now-previous.measured_at).total_seconds()
        if seconds>0:speed=distance(lat,lon,previous.latitude,previous.longitude)/seconds*3.6
    limit=p.event.radius_m+p.event.tolerance_m
    far=bool(previous and previous.distance_m>limit and d>limit)
    fast=speed is not None and speed>60
    r=LocationReading.objects.create(participant=p,latitude=lat,longitude=lon,accuracy_m=accuracy,distance_m=d,
        measured_at=now,speed_kmh=speed,anomalous=far or fast)
    if far or fast:
        LocationAnomaly.objects.create(participant=p,reading=r,criterion='DISTANCE' if far else 'SPEED')
        # Product decision for a single high-speed pair remains pending: persist the signal only.
        if far:notify_managers(p.event,'Sinal de movimentação anômala','Duas leituras além do limite. Investigação exige evento pausado ou encerrado; nenhuma sanção automática foi aplicada.')
    p.presence='PRESENT' if d<=p.event.radius_m else 'OUTSIDE' if d<=limit else 'DISTANT'
    p.location_consent=True;p.location_retry_count=0;p.location_failure_started_at=None;p.location_retry_exhausted_at=None
    p.location_last_attempt_at=now;p.location_next_due_at=now+timedelta(minutes=p.event.location_interval_minutes)
    if p.deactivation_reason=='GPS_TECHNICAL' and p.activated_at:
        p.is_active=True;p.registration_status='ACTIVE';p.deactivation_reason=''
        notify(p,'reactivation','Sua localização foi confirmada','Seu perfil foi reativado.')
    p.save();record(p.user,'location.validated',r,p.event)
    return p


@transaction.atomic
def failed(p,phase='periodic',now=None):
    now=now or timezone.now();p=EventParticipant.objects.select_for_update().select_related('event').get(pk=p.pk)
    if p.event.mode == 'ONLINE':
        return p
    if phase not in ['periodic','retry','manual']:raise ValidationError('Tentativa inválida.')
    if p.location_exception_until and now<p.location_exception_until:return p
    if not p.location_failure_started_at:
        p.location_failure_started_at=now;p.location_retry_count=0;p.location_last_attempt_at=now
        p.location_next_due_at=now+timedelta(minutes=p.event.location_interval_minutes)
    elif phase=='retry' and p.location_retry_count<5:
        if p.location_last_attempt_at and now<p.location_last_attempt_at+timedelta(minutes=1):
            raise ValidationError('Aguarde um minuto entre as tentativas de recuperação.')
        p.location_retry_count+=1;p.location_last_attempt_at=now
        if p.location_retry_count==5:p.location_retry_exhausted_at=now
    elif phase=='periodic' and p.location_retry_exhausted_at and p.location_next_due_at and now>=p.location_next_due_at:
        if p.is_active:
            p.is_active=False;p.registration_status='INACTIVE';p.deactivation_reason='GPS_TECHNICAL'
            notify(p,'gps_failure','Não conseguimos validar sua localização','Seu perfil foi temporariamente desativado. Tente novamente ou procure a equipe do evento.',key=f'gps:{p.pk}:{p.location_failure_started_at.isoformat()}',action_path='#mensagens')
    p.save();record(p.user,'location.failed',p,p.event,phase=phase,retries=p.location_retry_count)
    return p


@transaction.atomic
def exception(p,actor,minutes,reason,now=None):
    now=now or timezone.now()
    if not isinstance(minutes,int) or minutes<=0 or not reason.strip():raise ValidationError('Informe duração positiva em minutos e motivo.')
    p=EventParticipant.objects.select_for_update().select_related('event').get(pk=p.pk)
    if p.event.mode == 'ONLINE':
        raise ValidationError('Eventos online não utilizam exceções de GPS.')
    if p.deactivation_reason!='GPS_TECHNICAL':raise ValidationError('A exceção se aplica somente à falha técnica de GPS.')
    try:p.location_exception_until=now+timedelta(minutes=minutes)
    except OverflowError:raise ValidationError('Duração inválida.')
    p.is_active=True;p.registration_status='ACTIVE';p.save()
    obj=LocationException.objects.create(participant=p,actor=actor,reason=reason,expires_at=p.location_exception_until)
    record(actor,'location.exception',obj,p.event,minutes=minutes)
    notify(p,'reactivation','Seu perfil foi reativado temporariamente',f'Exceção de localização por {minutes} minutos. A tentativa manual permanece disponível.')
    return p


def expire_exceptions(now=None):
    now=now or timezone.now();count=0
    ids=EventParticipant.objects.filter(location_exception_until__lte=now,event__state__in=['OPEN','RUNNING','PAUSED']).exclude(event__mode='ONLINE').values_list('pk',flat=True)
    for pk in list(ids):
        with transaction.atomic():
            p=EventParticipant.objects.select_for_update().get(pk=pk)
            if not p.location_exception_until or p.location_exception_until>now:continue
            p.location_exception_until=None
            if p.deactivation_reason=='GPS_TECHNICAL':
                p.is_active=False;p.registration_status='INACTIVE'
                notify(p,'gps_exception_expired','A exceção de localização terminou','Tente validar sua localização novamente ou procure a equipe do evento.')
            p.save();record(None,'location.exception_expired',p,p.event);count+=1
    return count


def synchronize_online_presence(now=None):
    from django.db.models import Q
    from apps.events.models import Event
    now = now or timezone.now()
    count = 0
    for event in Event.objects.filter(mode='ONLINE', state__in=['OPEN', 'RUNNING', 'PAUSED']):
        cutoff = now - timedelta(minutes=event.location_interval_minutes)
        participants = EventParticipant.objects.filter(event=event)
        count += participants.filter(Q(last_seen_at__isnull=True) | Q(last_seen_at__lt=cutoff)).exclude(presence='ABSENT').update(presence='ABSENT')
        count += participants.filter(last_seen_at__gte=cutoff).exclude(presence='PRESENT').update(presence='PRESENT')
    return count
