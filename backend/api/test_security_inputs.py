"""Bounded attack payloads against a disposable test database and media root."""
import io
import tempfile
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.events.models import Event, EventAdministrator
from apps.matches.models import Match
from apps.messaging.models import Conversation, Message
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile

SQL = "' OR 1=1; DROP TABLE accounts_user; --"
XSS = '</script><img src=x onerror="window.__audit_xss=1">'


def image_upload(name='photo.png'):
    content = io.BytesIO()
    Image.new('RGB', (2, 2)).save(content, format='PNG')
    return SimpleUploadedFile(name, content.getvalue(), content_type='image/png')


class SecurityInputTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        settings = override_settings(MEDIA_ROOT=self.media.name)
        settings.enable()
        self.addCleanup(settings.disable)
        users = get_user_model()
        self.user = users.objects.create_user(username='audit@example.invalid', email='audit@example.invalid', password='Audit-safe-password-2026!')
        self.manager = users.objects.create_user(username='audit-manager', email='manager@example.invalid')
        self.event = Event.objects.create(organization=Organization.objects.create(name='Security audit'),
            name='Security audit', mode='ONLINE', state='RUNNING', ends_at=timezone.now()+timedelta(days=1))
        EventAdministrator.objects.create(event=self.event, user=self.manager)
        self.person = EventParticipant.objects.create(user=self.user, event=self.event, is_active=True)
        ParticipantProfile.objects.create(participant=self.person, first_name='Audit', last_name='Person', birth_month=1, birth_year=1995)
        peer = users.objects.create_user(username='audit-peer')
        self.peer = EventParticipant.objects.create(user=peer, event=self.event, is_active=True)
        ParticipantProfile.objects.create(participant=self.peer, first_name='Peer', last_name='Person', birth_month=1, birth_year=1995)
        first, second = sorted([self.person, self.peer], key=lambda p: p.pk.int)
        self.conversation = Conversation.objects.create(match=Match.objects.create(participant=first, partner=second))
        self.client = self.client_for(self.user)

    def client_for(self, user, csrf=False):
        client = APIClient(enforce_csrf_checks=csrf)
        client.force_login(user)
        session = client.session
        session['event_id'] = str(self.event.pk)
        session['navigation'] = 'participant' if user == self.user else 'administration'
        session.save()
        client.defaults['HTTP_X_EVENT_ID'] = str(self.event.pk)
        return client

    def test_sql_payloads_cannot_bypass_login(self):
        client = APIClient()
        for email, password in [(self.user.email, SQL), ("'or'1'='1@example.invalid", SQL), (SQL, SQL)]:
            response = client.post('/api/auth/login/', {'email': email, 'password': password}, format='json')
            self.assertEqual(response.status_code, 400, response.content)
            self.assertNotIn('_auth_user_id', client.session)
        self.assertEqual(get_user_model().objects.count(), 3)

    def test_sql_search_is_a_literal_and_does_not_expand_results(self):
        for payload in [SQL, "%' OR '1'='1", '"; SELECT pg_sleep(1); --', '%', '_', '\\']:
            with self.subTest(payload=payload), CaptureQueriesContext(connection) as queries:
                response = self.client.get('/api/participants/', {'search': payload})
                self.assertEqual(response.status_code, 200, response.content)
                self.assertEqual(response.json(), [])
                self.assertFalse(any(q['sql'].lstrip().upper().startswith(('DROP ', 'DELETE ', 'ALTER ')) for q in queries))
        self.assertEqual(EventParticipant.objects.count(), 2)

    def test_sql_and_xss_in_messages_are_stored_only_as_text(self):
        for payload in [SQL, XSS, '${7*7}', '{{7*7}}']:
            response = self.client.post(f'/api/conversations/{self.peer.pk}/messages/', {'text': payload}, format='json')
            self.assertEqual(response.status_code, 201, response.content)
            self.assertTrue(Message.objects.filter(conversation=self.conversation, body=payload).exists())
        self.assertEqual(EventParticipant.objects.count(), 2)

    def test_export_sql_preserves_quotes_backslashes_and_json_as_literal_values(self):
        from apps.events.export_snapshot import sql_snapshot
        value = SQL + " \\ ' " + XSS
        snapshot = {
            'schemas': {'audit.probe': {'table': 'audit_literal_probe',
                'columns': {'id': 'text', 'value': 'text', 'metadata': 'jsonb'}, 'relations': {}}},
            'records': {'audit.probe': [{'id': 'probe', 'value': value, 'metadata': {'payload': value}}]},
        }
        sql = sql_snapshot(snapshot)
        with connection.cursor() as cursor:
            cursor.execute('SAVEPOINT audit_sql_payload')
            try:
                cursor.execute(sql.removeprefix('BEGIN;').removesuffix('COMMIT;'))
                cursor.execute('SELECT value, metadata->>\'payload\' FROM event_export.audit_literal_probe')
                self.assertEqual(cursor.fetchone(), (value, value))
                cursor.execute('SELECT count(*) FROM public.accounts_user')
                self.assertEqual(cursor.fetchone()[0], 3)
            finally:
                cursor.execute('ROLLBACK TO SAVEPOINT audit_sql_payload')

    def test_typed_fields_reject_sql_and_nonnumeric_payloads(self):
        for value in [SQL, {'$gt': 0}, [18], 'NaN', 'Infinity']:
            response = self.client.put('/api/filters/', {'min': value, 'max': 100, 'gender': 'Todos', 'interests': [], 'purpose': ''}, format='json')
            self.assertEqual(response.status_code, 400, response.content)
        for value in [SQL, '../../etc/passwd', '00000000-0000-0000-0000-000000000000']:
            response = self.client.get('/api/event-admin/', HTTP_X_EVENT_ID=value)
            self.assertIn(response.status_code, [400, 404])
            self.assertNotIn(b'Traceback', response.content)

    def test_csrf_rejects_mutations_and_login_without_token(self):
        client = self.client_for(self.user, csrf=True)
        response = client.post(f'/api/conversations/{self.peer.pk}/messages/', {'text': 'forged'}, format='json', HTTP_ORIGIN='https://attacker.invalid')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Message.objects.filter(body='forged').exists())
        anonymous = APIClient(enforce_csrf_checks=True)
        self.assertEqual(anonymous.post('/api/auth/login/', {'email': self.user.email, 'password': 'Audit-safe-password-2026!'}, format='json').status_code, 403)

    def test_fake_invites_and_mass_assignment_do_not_grant_privileges(self):
        client = APIClient()
        self.assertEqual(client.post('/api/auth/register/', {'email': 'forged@example.invalid', 'password': 'Audit-strong-password-2026!', 'invite': str(self.event.pk)}, format='json').status_code, 400)
        token = signing.dumps(str(self.event.pk), salt='event-join')
        response = client.post('/api/auth/register/', {'email': 'new@example.invalid', 'password': 'Audit-strong-password-2026!',
            'invite': token, 'is_staff': True, 'is_superuser': True, 'role': 'ADMIN', 'navigation': 'global'}, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        created = get_user_model().objects.get(email='new@example.invalid')
        self.assertFalse(created.is_staff or created.is_superuser)
        self.assertFalse(created.event_administrations.exists())
        self.assertEqual(client.get('/api/global/').status_code, 403)

    def test_upload_rejects_svg_html_and_corrupt_images(self):
        for name, body, content_type in [('x.svg', b'<svg onload="alert(1)"/>', 'image/svg+xml'),
                ('x.html', b'<script>alert(1)</script>', 'image/png'), ('x.jpg', b'not a jpeg', 'image/jpeg')]:
            upload = SimpleUploadedFile(name, body, content_type=content_type)
            self.assertEqual(self.client.post('/api/profile/photos/', {'file': upload}, format='multipart').status_code, 400)
        self.assertEqual(list(Path(self.media.name).rglob('*')), [])

    def test_valid_image_uses_server_filename_not_traversal_or_executable_extension(self):
        response = self.client.post('/api/profile/photos/', {'file': image_upload('../../payload.php')}, format='multipart')
        self.assertEqual(response.status_code, 201, response.content)
        photo = self.person.photos.get()
        self.assertTrue(photo.storage_key.startswith(f'participants/{self.person.pk}/'))
        self.assertTrue(photo.storage_key.endswith('.png'))
        self.assertNotIn('payload', photo.storage_key)
        self.assertTrue(Path(self.media.name, photo.storage_key).is_file())

    def test_announcements_reject_executable_url_schemes(self):
        client = self.client_for(self.manager)
        for url in ['javascript:alert(1)', 'data:text/html,<script>alert(1)</script>', 'file:///etc/passwd']:
            response = client.post('/api/event-admin/announcements/', {'title': 'Audit', 'body': XSS, 'url': url}, format='json')
            self.assertEqual(response.status_code, 400, response.content)
