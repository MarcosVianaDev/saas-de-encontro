from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.audit.services import record
from apps.notifications.services import notify
from .models import ParticipantPass,PassUsage


def active_passes(p):
    return p.passes.filter(revoked_at__isnull=True).filter(Q(expires_at__isnull=True)|Q(expires_at__gt=timezone.now())).order_by('created_at','id')


def revealed_ids(p):
    return set(str(v) for v in PassUsage.objects.filter(participant_pass__participant=p).filter(
        Q(participant_pass__reveal_limit__isnull=False) |
        Q(participant_pass__reveal_limit__isnull=True,participant_pass__revoked_at__isnull=True,participant_pass__expires_at__gt=timezone.now())
    ).values_list('revealed_participant_id',flat=True))


@transaction.atomic
def reveal(p,candidates):
    from apps.participants.models import EventParticipant
    EventParticipant.objects.select_for_update().get(pk=p.pk)
    revealed=revealed_ids(p)
    peer=next((item for item in candidates if str(item.participant_id) not in revealed),None)
    if peer is None:raise ValidationError('Não há likes ocultos para revelar.')
    for participant_pass in active_passes(p).select_for_update():
        used=participant_pass.usages.count()
        if participant_pass.reveal_limit is not None and used>=participant_pass.reveal_limit:continue
        usage,created=PassUsage.objects.get_or_create(participant_pass=participant_pass,revealed_participant=peer.participant)
        if created:record(p.user,'pass.revealed',usage,p.event)
        return usage, None if participant_pass.reveal_limit is None else participant_pass.reveal_limit-participant_pass.usages.count()
    raise ValidationError('Não há passe válido ou saldo disponível. Procure o atendimento do evento.')


@transaction.atomic
def expire_passes(now=None):
    now=now or timezone.now();count=0
    for p in ParticipantPass.objects.select_for_update().filter(expires_at__lte=now,expiry_notified_at__isnull=True,revoked_at__isnull=True).select_related('participant__event'):
        notify(p.participant,'pass_expired','Seu passe expirou','Seus likes continuam salvos. Você pode adquirir outro passe para revelar os que permanecem ocultos.',key=f'pass-expired:{p.pk}',action_path='#participantes')
        p.expiry_notified_at=now;p.save(update_fields=['expiry_notified_at','updated_at'])
        record(None,'pass.expired',p,p.participant.event);count+=1
    return count
