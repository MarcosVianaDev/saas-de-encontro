import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.audit.services import record
from apps.events.models import Event, ExportJob, EventAdministrator
from apps.events.export_service import artifact, generate_export
from apps.events.export_snapshot import MODULES
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ParticipantPhoto
from apps.reports.models import Report
from apps.passes.models import PassType, EventPassOffer, ParticipantPass


class EventExportTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.media.cleanup)
        self.settings_override = override_settings(EXPORT_BACKUP_ROOT=self.directory.name, MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        User = get_user_model()
        self.admin = User.objects.create_user(username='global', email='global@example.com', is_superuser=True)
        self.user = User.objects.create_user(username='shared', email='shared@example.com', password='never-export-this')
        self.org = Organization.objects.create(name='Shared org')
        self.event = Event.objects.create(name='Export target', organization=self.org, responsible=self.admin, mode='ONLINE')
        self.other = Event.objects.create(name='PRIVATE_OTHER_EVENT', organization=self.org, mode='ONLINE')
        self.p = EventParticipant.objects.create(event=self.event, user=self.user)
        self.other_p = EventParticipant.objects.create(event=self.other, user=self.user)
        ParticipantProfile.objects.create(participant=self.p, first_name='Target', last_name='Person')
        ParticipantProfile.objects.create(participant=self.other_p, first_name='PRIVATE_PERSON', last_name='Other')
        Report.objects.create(reported=self.other_p, reason='PRIVATE_REPORT', description='PRIVATE_DESCRIPTION')
        Path(self.media.name, 'photo.jpg').write_bytes(b'photo-content')
        ParticipantPhoto.objects.create(participant=self.p, storage_key='photo.jpg')
        ParticipantPhoto.objects.create(participant=self.p, storage_key='missing.jpg')
        offer = EventPassOffer.objects.create(event=self.event, pass_type=PassType.objects.create(name='Temporal', duration=timedelta(minutes=30)), price=0)
        ParticipantPass.objects.create(participant=self.p, offer=offer, expires_at=timezone.now() + timedelta(minutes=30))
        record(self.admin, 'target.action', self.p, self.event)
        record(self.admin, 'PRIVATE_OTHER_AUDIT', self.other_p, self.other)
        self.client = APIClient()
        self.client.force_login(self.admin)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session.save()

    def job(self):
        return ExportJob.objects.create(event=self.event, requested_by=self.admin, modules=MODULES)

    def test_request_is_async_deduplicated_and_enqueued_after_commit(self):
        with patch('apps.events.export_tasks.generate.delay') as queued, self.captureOnCommitCallbacks(execute=True):
            first = self.client.post('/api/event-admin/exports/', {}, format='json')
            second = self.client.post('/api/event-admin/exports/', {}, format='json')
            self.assertEqual(first.status_code, 202, first.content)
            self.assertEqual(first.json()['id'], second.json()['id'])
            queued.assert_not_called()
        queued.assert_called_once()
        self.assertEqual(ExportJob.objects.get().state, 'PENDING')
        self.assertFalse(artifact(ExportJob.objects.get(), 'event.zip').exists())

    def test_zip_offline_sql_hashes_pdf_media_and_event_isolation(self):
        job = self.job()
        self.assertEqual(generate_export(job.pk), 'COMPLETED')
        job.refresh_from_db()
        with zipfile.ZipFile(artifact(job, 'event.zip')) as archive:
            self.assertNotIn('term.pdf', archive.namelist())
            manifest = json.loads(archive.read('manifest.json'))
            snapshot = json.loads(archive.read('snapshot.json'))
            for path, info in manifest['files'].items():
                self.assertEqual(hashlib.sha256(archive.read(path)).hexdigest(), info['sha256'])
            self.assertEqual(len(snapshot['records']['participants.eventparticipant']), 1)
            self.assertTrue(manifest['missingMedia'])
            self.assertEqual(len(snapshot['media']), 1)
            sql = archive.read('event.sql').decode()
            html = archive.read('index.html').decode()
            for forbidden in ['PRIVATE_OTHER_EVENT', 'PRIVATE_PERSON', 'PRIVATE_REPORT', 'PRIVATE_OTHER_AUDIT', self.user.password]:
                self.assertNotIn(forbidden, sql + html)
            self.assertNotIn('fetch(', html)
            self.assertIn("connect-src 'none'", html)
            self.assertIn('CREATE SCHEMA', sql)
            self.assertTrue(snapshot['records']['audit.auditlog'])
            # Real PostgreSQL import: all schema/tables/relations are queryable.
            with connection.cursor() as cursor:
                cursor.execute('SAVEPOINT export_restore_test')
                try:
                    # Strip transaction wrapper; do not commit the Django test.
                    cursor.execute(sql.removeprefix('BEGIN;').removesuffix('COMMIT;'))
                    cursor.execute('SELECT COUNT(*) FROM event_export.participants_eventparticipant')
                    self.assertEqual(cursor.fetchone()[0], 1)
                finally:
                    cursor.execute('ROLLBACK TO SAVEPOINT export_restore_test')
        pdf = artifact(job, 'term.pdf').read_bytes()
        self.assertTrue(pdf.startswith(b'%PDF-'))
        self.assertIn(job.zip_sha256.encode(), pdf)
        self.assertEqual(generate_export(job.pk), 'COMPLETED')
        self.assertEqual(AuditLog.objects.filter(action='export.completed').count(), 1)

    def test_status_and_download_authorization_event_scope_and_audit(self):
        job = self.job()
        generate_export(job.pk)
        url = f'/api/event-admin/exports/{job.pk}/download/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b''.join(response.streaming_content).startswith(b'PK'))
        self.assertTrue(AuditLog.objects.filter(action='export.downloaded').exists())
        for role in ['ADMIN', 'MODERATOR', 'OPERATOR']:
            user = get_user_model().objects.create_user(username=role, is_staff=True)
            EventAdministrator.objects.create(event=self.event, user=user, role=role)
            self.client.force_login(user)
            session = self.client.session
            session['event_id'] = str(self.event.pk)
            session.save()
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post('/api/event-admin/exports/', {}, format='json').status_code, 403)
        self.client.force_login(self.admin)
        session = self.client.session
        session['event_id'] = str(self.other.pk)
        session.save()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_failure_retry_and_broker_failure_are_public_safe(self):
        job = self.job()
        with patch('apps.events.export_service.collect', side_effect=RuntimeError('private detail')):
            with self.assertRaises(RuntimeError):
                generate_export(job.pk)
        job.refresh_from_db()
        self.assertEqual(job.state, 'FAILED')
        self.assertNotIn('private detail', job.error)
        self.assertFalse(artifact(job, 'working').exists())
        with patch('apps.events.export_tasks.generate.delay', side_effect=RuntimeError('broker')):
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(self.client.post(f'/api/event-admin/exports/{job.pk}/', {'action': 'retry'}, format='json').status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.state, 'FAILED')

    def test_tampered_download_is_blocked(self):
        job = self.job()
        generate_export(job.pk)
        artifact(job, 'event.zip').write_bytes(b'tampered')
        self.assertEqual(self.client.get(f'/api/event-admin/exports/{job.pk}/download/').status_code, 400)

    def test_audit_failure_never_publishes_success_or_artifacts(self):
        job = self.job()
        with patch('apps.audit.services.AuditLog.objects.create', side_effect=RuntimeError('audit unavailable')):
            with self.assertRaises(Exception):
                generate_export(job.pk)
        job.refresh_from_db()
        self.assertEqual(job.state, 'FAILED')
        self.assertFalse(artifact(job, 'event.zip').exists())

    def test_expired_export_creates_new_job_preserving_original(self):
        job = self.job()
        generate_export(job.pk)
        job.refresh_from_db()
        original = artifact(job, 'event.zip').read_bytes()
        ExportJob.objects.filter(pk=job.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        url = f'/api/event-admin/exports/{job.pk}/'
        with patch('apps.events.export_tasks.generate.delay'), self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, {'action': 'retry'}, format='json')
        self.assertEqual(response.status_code, 202)
        self.assertNotEqual(response.json()['id'], str(job.pk))
        self.assertEqual(artifact(job, 'event.zip').read_bytes(), original)

    def test_signed_term_and_delivery_are_registered_and_audited(self):
        job = self.job()
        generate_export(job.pk)
        url = f'/api/event-admin/exports/{job.pk}/'
        self.assertEqual(self.client.post(url, {'action': 'delivery', 'reference': 'Receipt'}, format='json').status_code, 400)
        upload = SimpleUploadedFile('signed.pdf', b'%PDF-1.4\nexternal-signature', content_type='application/pdf')
        response = self.client.post(url, {'action': 'signature', 'reference': 'External signing receipt', 'file': upload}, format='multipart')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.client.post(url, {'action': 'delivery', 'reference': 'Delivery receipt'}, format='json').status_code, 200)
        self.assertTrue(AuditLog.objects.filter(action='export.signature_recorded').exists())
        self.assertTrue(AuditLog.objects.filter(action='export.delivery_recorded').exists())

    def test_custom_scope_keeps_audit_and_legal_hold_dependencies(self):
        from apps.retention.models import LegalHold
        LegalHold.objects.create(participant=self.p, reason='Preservação do evento')
        job = ExportJob.objects.create(event=self.event, requested_by=self.admin, modules=['audit'])
        generate_export(job.pk)
        with zipfile.ZipFile(artifact(job, 'event.zip')) as archive:
            snapshot = json.loads(archive.read('snapshot.json'))
            self.assertTrue(snapshot['records']['retention.legalhold'])
            self.assertTrue(snapshot['records']['audit.auditlog'])
            self.assertNotIn('profiles.participantprofile', snapshot['records'])
