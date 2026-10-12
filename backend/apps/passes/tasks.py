from celery import shared_task
from .services import expire_passes

@shared_task
def expire():return expire_passes()


@shared_task
def initial_gifts():
    from .gifts import grant_due_initial_gifts
    return grant_due_initial_gifts()
