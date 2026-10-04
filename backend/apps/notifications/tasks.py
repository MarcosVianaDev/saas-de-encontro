from celery import shared_task
from .announcements import dispatch_due

@shared_task
def dispatch_announcements():return dispatch_due()
