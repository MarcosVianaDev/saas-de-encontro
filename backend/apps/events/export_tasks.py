from celery import shared_task
from django.db import transaction
from apps.audit.services import record
from .models import ExportJob
from .export_service import generate_export


@shared_task(bind=True, max_retries=2, acks_late=True, queue='exports')
def generate(self, identifier):
    try:
        return generate_export(identifier)
    except Exception as error:
        if self.request.retries < self.max_retries:
            with transaction.atomic():
                job = ExportJob.objects.select_for_update().get(pk=identifier)
                if job.state == 'FAILED':
                    job.state, job.stage = 'PENDING', 'Aguardando nova tentativa do Celery'
                    job.save()
                    record(None, 'export.retry_scheduled', job, job.event)
            raise self.retry(exc=error, countdown=30 * (2 ** self.request.retries))
        raise
