from celery import shared_task
from .services import expire_passes

@shared_task
def expire():return expire_passes()
