from celery import shared_task
from .services import synchronize


@shared_task
def synchronize_events():
    from apps.participants.location import expire_exceptions, synchronize_online_presence
    expire_exceptions()
    synchronize_online_presence()
    return synchronize()
