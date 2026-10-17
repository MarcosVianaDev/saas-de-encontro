import logging
from datetime import timedelta
from time import monotonic
from uuid import uuid4

from celery import shared_task
from django.conf import settings
from django.db import OperationalError
from django.utils import timezone
from kombu.exceptions import OperationalError as BrokerOperationalError

from apps.participants.models import EventParticipant
from .models import InitialGiftSweep
from .services import expire_passes

logger = logging.getLogger(__name__)
GIFT_LEASE_SECONDS = 120
GIFT_BATCH_SECONDS = 5


@shared_task
def expire():return expire_passes()


@shared_task
def initial_gifts():
    """Beat only acquires a lease and publishes one bounded delivery task."""
    now = timezone.now()
    token = uuid4()
    InitialGiftSweep.objects.get_or_create(pk=1, defaults={'expires_at': now})
    acquired = InitialGiftSweep.objects.filter(pk=1, expires_at__lte=now).update(
        token=token, cursor=None, expires_at=now + timedelta(seconds=GIFT_LEASE_SECONDS),
    )
    if not acquired:
        return False
    try:
        initial_gift_batch.delay(str(token))
    except Exception:
        InitialGiftSweep.objects.filter(pk=1, token=token).update(expires_at=timezone.now())
        raise
    return True


@shared_task(queue='gifts', acks_late=True, reject_on_worker_lost=True,
             autoretry_for=(OperationalError, BrokerOperationalError),
             retry_backoff=True, retry_backoff_max=30, max_retries=3)
def initial_gift_batch(token, after=None):
    from .gifts import due_initial_gift_participants, grant_initial_gift

    now = timezone.now()
    sweep = InitialGiftSweep.objects.filter(pk=1, token=token, cursor=after)
    if not sweep.filter(expires_at__gt=now).update(
        expires_at=now + timedelta(seconds=GIFT_LEASE_SECONDS),
    ):
        return 0  # An expired/replayed task cannot restart an obsolete sweep.

    size = settings.INITIAL_GIFT_BATCH_SIZE
    identifiers = list(due_initial_gift_participants(now, after=after).values_list('pk', flat=True)[:size + 1])
    granted = 0
    cursor = None
    started = monotonic()
    for identifier in identifiers[:size]:
        try:
            # Re-read eligibility and the clock inside each atomic grant. Queued
            # tasks must not grant after event closure or participant removal.
            granted += grant_initial_gift(EventParticipant(pk=identifier))
        except OperationalError:
            raise  # Retry transient database failures without advancing the cursor.
        except Exception:
            # A broken participant must not starve everybody behind its cursor.
            # The next Beat sweep retries any participant still without a gift.
            logger.exception('Initial gift failed for participant %s', identifier)
        cursor = identifier
        if monotonic() - started >= GIFT_BATCH_SECONDS:
            break

    if cursor is not None and (len(identifiers) > size or cursor != identifiers[-1]):
        # Only one delivery of a duplicated batch may publish the continuation.
        if sweep.update(cursor=cursor):
            try:
                initial_gift_batch.delay(token, str(cursor))
            except Exception:
                InitialGiftSweep.objects.filter(pk=1, token=token, cursor=cursor).update(
                    expires_at=timezone.now(),
                )
                raise
    else:
        sweep.update(expires_at=timezone.now())
    return granted
