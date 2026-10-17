import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.test import TestCase, SimpleTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.events.models import Event, EventAdministrator
from apps.matches.models import Match
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantPhoto, ParticipantProfile, EventOutfitPhoto
from apps.reports.models import Block, Report, ReportEvidence
from .protected_media import INTERNAL_MEDIA_PREFIX, protected_media_response


@override_settings(MEDIA_USE_X_ACCEL_REDIRECT=True)
class ProtectedMediaPathTests(SimpleTestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(override_settings(MEDIA_ROOT=self.root))

    def write(self, key, content=b'file bytes'):
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_offload_returns_empty_body_headers_and_never_opens_file(self):
        self.write('photos/image.jpg')
        with patch('api.protected_media.default_storage.open', side_effect=AssertionError('Python must not open the media')):
            response = protected_media_response('photos/image.jpg')
        self.assertFalse(response.streaming)
        self.assertEqual(response.content, b'')
        self.assertEqual(response['X-Accel-Redirect'], INTERNAL_MEDIA_PREFIX + 'photos/image.jpg')
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')

    def test_escaped_names_and_attachment_disposition(self):
        key = 'evidence/olá 100% #?.png'
        self.write(key)
        response = protected_media_response(key, as_attachment=True)
        self.assertEqual(response['X-Accel-Redirect'], INTERNAL_MEDIA_PREFIX + quote(key, safe='/'))
        self.assertTrue(response['Content-Disposition'].startswith('attachment;'))
        self.assertIn("filename*=utf-8''", response['Content-Disposition'])
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_rejects_traversal_absolute_windows_control_and_empty_paths(self):
        for key in ['', '../outside', 'one/../two', '/etc/passwd', '//server/file', 'a//b', './file',
                    'C:/secret', 'C:\\secret', 'a\\b', 'a\x00.jpg', 'a\r\nX-Header:1.jpg', None]:
            with self.subTest(key=key), self.assertRaises(Http404):
                protected_media_response(key)

    def test_missing_files_and_directories_are_404(self):
        (self.root / 'directory').mkdir()
        for key in ['missing.jpg', 'directory']:
            with self.subTest(key=key), self.assertRaises(Http404):
                protected_media_response(key)

    def test_symlinks_to_files_and_directories_are_rejected(self):
        normal = self.write('normal.jpg')
        (self.root / 'link.jpg').symlink_to(normal)
        with tempfile.TemporaryDirectory() as outside:
            Path(outside, 'secret.jpg').write_bytes(b'outside')
            (self.root / 'escape').symlink_to(outside, target_is_directory=True)
            for key in ['link.jpg', 'escape/secret.jpg']:
                with self.subTest(key=key), self.assertRaises(Http404):
                    protected_media_response(key)

    @override_settings(MEDIA_USE_X_ACCEL_REDIRECT=False)
    def test_explicit_direct_development_fallback_streams_the_file(self):
        self.write('fallback.png', b'image')
        response = protected_media_response('fallback.png')
        try:
            self.assertNotIn('X-Accel-Redirect', response)
            self.assertEqual(b''.join(response.streaming_content), b'image')
        finally:
            response.close()

    @override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'}})
    def test_nonlocal_storage_cannot_use_the_nginx_local_alias(self):
        with self.assertRaises(ImproperlyConfigured):
            protected_media_response('photo.jpg')


@override_settings(MEDIA_USE_X_ACCEL_REDIRECT=True)
class ProtectedMediaAuthorizationTests(TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(override_settings(MEDIA_ROOT=self.root))
        self.event = Event.objects.create(organization=Organization.objects.create(name='Client'), name='Event', mode='ONLINE', state='RUNNING')
        self.other_event = Event.objects.create(organization=self.event.organization, name='Other', mode='ONLINE', state='RUNNING')
        self.owner = get_user_model().objects.create_user(username='owner')
        self.membership = EventAdministrator.objects.create(user=self.owner, event=self.event, role='ADMIN')
        self.actor = self.participant('actor')
        self.peer = self.participant('peer')
        self.foreign = self.participant('foreign', self.other_event)
        self.photo = self.photo_for(self.peer, 'public.jpg')
        self.private = self.photo_for(self.peer, 'private.jpg', visibility='POST_MATCH')
        self.own = self.photo_for(self.actor, 'own.jpg')
        self.outfit = EventOutfitPhoto.objects.create(participant=self.peer, storage_key='outfit.jpg')
        self.write('outfit.jpg')
        self.report = Report.objects.create(reporter=self.actor, reported=self.peer, reason='Reason')
        self.evidence = ReportEvidence.objects.create(report=self.report, storage_key='evidence.txt')
        self.write('evidence.txt')
        self.client = APIClient()
        self.client.force_login(self.actor.user)

    def participant(self, name, event=None):
        p = EventParticipant.objects.create(event=event or self.event, user=get_user_model().objects.create_user(username=name), is_active=True)
        ParticipantProfile.objects.create(participant=p, first_name=name)
        return p

    def write(self, key):
        (self.root / key).write_bytes(b'private file')

    def photo_for(self, p, key, **kwargs):
        self.write(key)
        return ParticipantPhoto.objects.create(participant=p, storage_key=key, **kwargs)

    def url(self, suffix, event=None):
        return f'/api/events/{(event or self.event).pk}/{suffix}'

    def matched(self):
        first, second = sorted([self.actor, self.peer], key=lambda p: p.pk.int)
        return Match.objects.create(participant=first, partner=second)

    def assert_accelerated(self, response, key):
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(response.streaming)
        self.assertEqual(response.content, b'')
        self.assertEqual(response['X-Accel-Redirect'], INTERNAL_MEDIA_PREFIX + key)

    def test_self_and_public_photos_are_authorized_without_opening_in_python(self):
        with patch('api.protected_media.default_storage.open', side_effect=AssertionError('No streaming')):
            for photo in [self.own, self.photo]:
                self.assert_accelerated(self.client.get(self.url(f'photos/{photo.pk}/content/')), photo.storage_key)

    def test_private_photos_and_outfits_require_active_match_and_respect_block(self):
        urls = [self.url(f'photos/{self.private.pk}/content/'), self.url(f'outfits/{self.peer.pk}/content/')]
        for url in urls:
            self.assertIn(self.client.get(url).status_code, [403, 404])
        match = self.matched()
        for url, key in zip(urls, ['private.jpg', 'outfit.jpg']):
            self.assert_accelerated(self.client.get(url), key)
        match.is_active = False
        match.save()
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        match.is_active = True
        match.save()
        Block.objects.create(participant=self.actor, target=self.peer)
        for url in urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [403, 404])
            self.assertNotIn('X-Accel-Redirect', response)

    def test_anonymous_other_event_removed_and_placeholder_photos_never_offload(self):
        foreign = self.photo_for(self.foreign, 'foreign.jpg')
        ParticipantPhoto.objects.filter(pk=self.photo.pk).update(removed_at=timezone.now())
        placeholder = ParticipantPhoto.objects.create(participant=self.actor, storage_key='/images/example.jpg')
        for photo in [foreign, self.photo, placeholder]:
            response = self.client.get(self.url(f'photos/{photo.pk}/content/'))
            self.assertEqual(response.status_code, 404)
            self.assertNotIn('X-Accel-Redirect', response)
        self.client.logout()
        response = self.client.get(self.url(f'photos/{self.own.pk}/content/'))
        self.assertEqual(response.status_code, 401)
        self.assertNotIn('X-Accel-Redirect', response)

    def test_admin_photos_preserve_event_visibility_and_membership_checks(self):
        self.client.force_login(self.owner)
        self.assert_accelerated(self.client.get(self.url(f'event-admin/photos/{self.photo.pk}/content/')), 'public.jpg')
        for path in [self.url(f'event-admin/photos/{self.private.pk}/content/'),
                     self.url(f'event-admin/photos/{self.photo.pk}/content/', self.other_event)]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404)
            self.assertNotIn('X-Accel-Redirect', response)
        EventAdministrator.objects.filter(pk=self.membership.pk).update(is_active=False)
        response = self.client.get(self.url(f'event-admin/photos/{self.photo.pk}/content/'))
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('X-Accel-Redirect', response)

    def test_evidence_is_downloaded_only_after_authorization_and_audit(self):
        self.client.force_login(self.owner)
        url = self.url(f'event-admin/evidence/{self.evidence.pk}/content/')
        response = self.client.get(url)
        self.assert_accelerated(response, 'evidence.txt')
        self.assertTrue(response['Content-Disposition'].startswith('attachment;'))
        self.assertTrue(AuditLog.objects.filter(action='evidence.viewed', object_id=self.evidence.pk).exists())
        EventAdministrator.objects.filter(pk=self.membership.pk).update(role='OPERATOR')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('X-Accel-Redirect', response)

    def test_audit_failure_never_returns_a_media_redirect(self):
        self.client.force_login(self.owner)
        with patch('apps.audit.services.AuditLog.objects.create', side_effect=RuntimeError('Audit down')):
            response = self.client.get(self.url(f'event-admin/evidence/{self.evidence.pk}/content/'))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('X-Accel-Redirect', response)
