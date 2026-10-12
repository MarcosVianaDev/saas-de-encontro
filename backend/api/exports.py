import os
from datetime import timedelta

from django.db import transaction, connection
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record
from apps.events.models import Event, ExportJob
from apps.events.export_snapshot import MODULES, digest
from apps.events.export_service import artifact, export_lock_key
from apps.events.export_tasks import generate
from .global_admin import authorize


class ExportRequestSerializer(serializers.Serializer):
    reference = serializers.CharField(max_length=500, required=False, allow_blank=True, default='Teste pela administração global')
    modules = serializers.ListField(child=serializers.ChoiceField(choices=MODULES), required=False, default=MODULES, allow_empty=False)


def payload(job):
    return {'id': str(job.pk), 'event': str(job.event_id), 'state': job.state, 'status': job.get_state_display(),
        'progress': job.progress, 'stage': job.stage, 'error': job.error,
        'attempts': job.attempts, 'created': job.created_at, 'finished': job.finished_at,
        'canRetry': job.state == 'FAILED' or job.state == 'PROCESSING' and job.updated_at < timezone.now() - timedelta(hours=1),
        'expires': job.expires_at, 'sha256': job.zip_sha256,
        'download': f'/api/event-admin/exports/{job.pk}/download/' if job.state == 'COMPLETED' else None,
        'term': f'/api/event-admin/exports/{job.pk}/download/?artifact=pdf' if job.state == 'COMPLETED' else None}


def event_for(request):
    authorize(request)
    return get_object_or_404(Event, pk=request.session.get('event_id'))


def job_for(request, identifier):
    event = event_for(request)
    return get_object_or_404(ExportJob, pk=identifier, event=event)


def enqueue(identifier):
    try:
        generate.delay(str(identifier))
    except Exception:
        with transaction.atomic():
            job = ExportJob.objects.select_for_update().get(pk=identifier)
            if job.state == 'PENDING':
                job.state, job.error, job.stage = 'FAILED', 'Não foi possível agendar a exportação. Tente novamente.', 'Celery indisponível'
                job.save()
                record(None, 'export.enqueue_failed', job, job.event)


class EventExportsView(APIView):
    def get(self, request):
        event = event_for(request)
        job = event.exports.order_by('-created_at').first()
        return Response(payload(job) if job else None)

    @transaction.atomic
    def post(self, request):
        event = Event.objects.select_for_update().get(pk=event_for(request).pk)
        serializer = ExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = event.exports.filter(state__in=['PENDING', 'PROCESSING']).first()
        if not job:
            values = serializer.validated_data
            job = ExportJob.objects.create(event=event, requested_by=request.user, reference=values['reference'],
                modules=list(dict.fromkeys([*values['modules'], 'audit'])))
            record(request.user, 'export.requested', job, event, reference=job.reference, modules=job.modules)
            transaction.on_commit(lambda: enqueue(job.pk))
        return Response(payload(job), status=202)


class ExportStatusView(APIView):
    def get(self, request, identifier):
        return Response(payload(job_for(request, identifier)))

    @transaction.atomic
    def post(self, request, identifier):
        job = ExportJob.objects.select_for_update().get(pk=job_for(request, identifier).pk)
        action = request.data.get('action', 'retry')
        if action == 'retry':
            stale = job.state == 'PROCESSING' and job.updated_at < timezone.now() - timedelta(hours=1)
            expired = job.state == 'COMPLETED' and job.expires_at and job.expires_at <= timezone.now()
            if job.state != 'FAILED' and not stale and not expired:
                raise ValidationError('A exportação não está disponível para nova tentativa.')
            if expired:
                Event.objects.select_for_update().get(pk=job.event_id)
                active = job.event.exports.filter(state__in=['PENDING', 'PROCESSING']).first()
                if not active:
                    active = ExportJob.objects.create(event=job.event, requested_by=request.user, reference=job.reference, modules=job.modules)
                    record(request.user, 'export.requested', active, active.event, previous_export=str(job.pk), modules=active.modules)
                    transaction.on_commit(lambda: enqueue(active.pk))
                return Response(payload(active), status=202)
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_try_advisory_xact_lock(%s)', [export_lock_key(job.pk)])
                    if not cursor.fetchone()[0]:
                        raise ValidationError('O worker ainda está processando esta exportação.')
            Event.objects.select_for_update().get(pk=job.event_id)
            if job.event.exports.filter(state__in=['PENDING', 'PROCESSING']).exclude(pk=job.pk).exists():
                raise ValidationError('Já existe outra exportação em andamento.')
            job.state, job.progress, job.stage, job.error = 'PENDING', 0, 'Aguardando Celery', ''
            job.zip_path = job.pdf_path = job.zip_sha256 = job.pdf_sha256 = ''
            job.signed_pdf_path = job.signed_pdf_sha256 = job.signature_reference = job.delivery_reference = ''
            job.manifest = {}
            job.save()
            record(request.user, 'export.retry_requested', job, job.event)
            transaction.on_commit(lambda: enqueue(job.pk))
        elif action == 'signature':
            if job.signed_pdf_path:
                raise ValidationError('A assinatura já foi registrada. O termo original não pode ser sobrescrito.')
            upload = request.FILES.get('file')
            reference = serializers.CharField(max_length=500).run_validation(request.data.get('reference'))
            if job.state != 'COMPLETED' or not upload or upload.size > 10 * 1024 * 1024 or upload.read(5) != b'%PDF-':
                raise ValidationError('Envie o termo assinado em PDF após concluir a exportação (até 10 MB).')
            upload.seek(0)
            path = artifact(job, 'signed-term.pdf')
            with path.open('wb') as output:
                for chunk in upload.chunks():
                    output.write(chunk)
            os.chmod(path, 0o600)
            job.signed_pdf_path, job.signed_pdf_sha256, job.signature_reference = str(path.relative_to(path.parent.parent)), digest(path), reference
            job.save()
            record(request.user, 'export.signature_recorded', job, job.event, reference=reference, sha256=job.signed_pdf_sha256)
        elif action == 'delivery':
            if job.state != 'COMPLETED' or not job.signature_reference:
                raise ValidationError('Registre a assinatura antes do encaminhamento formal.')
            reference = serializers.CharField(max_length=500).run_validation(request.data.get('reference'))
            job.delivery_reference = reference
            job.save()
            record(request.user, 'export.delivery_recorded', job, job.event, reference=reference, sha256=job.zip_sha256)
        else:
            raise ValidationError('Ação inválida.')
        return Response(payload(job))


class ExportDownloadView(APIView):
    def get(self, request, identifier):
        with transaction.atomic():
            job = job_for(request, identifier)
            if job.state != 'COMPLETED' or job.expires_at and job.expires_at <= timezone.now():
                raise PermissionDenied('Exportação indisponível ou com prazo de download expirado.')
            kind = request.query_params.get('artifact', 'zip')
            choices = {'zip': ('event.zip', job.zip_sha256, 'application/zip'),
                'pdf': ('term.pdf', job.pdf_sha256, 'application/pdf'),
                'signed': ('signed-term.pdf', job.signed_pdf_sha256, 'application/pdf')}
            if kind not in choices:
                raise ValidationError('Artefato inválido.')
            name, expected, content_type = choices[kind]
            path = artifact(job, name)
            if not expected or not path.is_file() or digest(path) != expected:
                raise ValidationError('Arquivo indisponível ou integridade inválida. Gere uma nova exportação.')
            record(request.user, 'export.downloaded', job, job.event, artifact=kind, sha256=expected)
            response = FileResponse(path.open('rb'), as_attachment=True,
                filename=f'evento-{job.event_id}-{job.pk}.{ "zip" if kind == "zip" else "pdf"}', content_type=content_type)
            response['Cache-Control'] = 'private, no-store'
            response['X-Content-Type-Options'] = 'nosniff'
            return response
