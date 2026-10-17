"""Explicit audit observations, not security assertions or default test discovery.

Run only with `manage.py test security_review`; every probe rolls back its data.
FINDING lines describe current behavior, including weaknesses, without teaching
the ordinary regression suite to require a vulnerability to remain present.
"""
import json
import io
from pathlib import Path
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.throttling import SimpleRateThrottle

from api import test_security_inputs as fixtures
from apps.events.models import Event, EventAdministrator
from apps.moderation.models import UserSuspension


def observation(identifier, **data):
    print('SECURITY_OBSERVATION ' + json.dumps({'id': identifier, **data}, sort_keys=True), flush=True)


class AuthenticationObservations(TestCase):
    def test_admin_login_attempt_budget(self):
        client = Client(enforce_csrf_checks=True)
        client.get('/mcx/login/')
        csrf = client.cookies['csrftoken'].value
        statuses = [client.post('/mcx/login/', {'username': 'audit-admin@example.invalid',
            'password': 'Incorrect-audit-password', 'csrfmiddlewaretoken': csrf}).status_code for _ in range(12)]
        self.assertTrue(all(status in [200, 429, 403] for status in statuses))
        observation('ADMIN_LOGIN_THROTTLE', attempts=12, statuses=statuses, limited=any(status in [403, 429] for status in statuses))

    def test_api_login_ip_rotation_budget(self):
        from rest_framework.test import APIClient
        client = APIClient()
        cache.clear()
        with patch.dict(SimpleRateThrottle.THROTTLE_RATES, {'login': '3/min', 'anon': '60/min'}):
            fixed = [client.post('/api/auth/login/', {'email': 'audit@example.invalid', 'password': 'wrong'},
                format='json', HTTP_X_FORWARDED_FOR='192.0.2.1, 172.18.0.1').status_code for _ in range(4)]
            rotated = [client.post('/api/auth/login/', {'email': 'audit@example.invalid', 'password': 'wrong'},
                format='json', HTTP_X_FORWARDED_FOR=f'192.0.2.{index}, 172.18.0.1').status_code for index in range(2, 7)]
        observation('LOGIN_ACCOUNT_BUDGET', fixed_ip=fixed, different_ips=rotated)


class StorageObservations(TestCase):
    setUp = fixtures.SecurityInputTests.setUp
    client_for = fixtures.SecurityInputTests.client_for
    def test_photo_retention_budget(self):
        codes = []
        for _ in range(12):
            response = self.client.post('/api/profile/photos/', {'file': fixtures.image_upload()}, format='multipart')
            codes.append(response.status_code)
            if response.status_code != 201:
                break
            url = response.json()['photos'][-1]
            self.assertEqual(self.client.delete('/api/profile/photos/', {'url': url}, format='json').status_code, 200)
        files = [path for path in Path(self.media.name).rglob('*') if path.is_file()]
        observation('PHOTO_RETAINED_STORAGE', accepted=codes.count(201), active=self.person.photos.filter(removed_at__isnull=True).count(),
            retained_files=len(files), retained_bytes=sum(path.stat().st_size for path in files))

    def test_photo_gps_metadata(self):
        exif = Image.Exif()
        exif[0x8825] = {1: 'S', 2: (23.0, 33.0, 0.0), 3: 'W', 4: (46.0, 38.0, 0.0)}
        content = io.BytesIO()
        Image.new('RGB', (2, 2)).save(content, format='JPEG', exif=exif)
        response = self.client.post('/api/profile/photos/', {'file': SimpleUploadedFile('gps.jpg', content.getvalue(), content_type='image/jpeg')}, format='multipart')
        self.assertEqual(response.status_code, 201, response.content)
        photo = self.person.photos.get()
        # Complete public photos, then model the approved profile so another
        # participant can access the actual protected-media endpoint.
        for _ in range(2):
            self.assertEqual(self.client.post('/api/profile/photos/', {'file': fixtures.image_upload()}, format='multipart').status_code, 201)
        self.person.is_active = True
        self.person.save()
        peer_client = self.client_for(self.peer.user)
        response = peer_client.get(f'/api/events/{self.event.pk}/photos/{photo.pk}/content/')
        self.assertEqual(response.status_code, 200)
        downloaded = b''.join(response.streaming_content)
        gps = Image.open(io.BytesIO(downloaded)).getexif().get_ifd(0x8825)
        observation('PROFILE_PHOTO_GPS_METADATA', other_participant_downloaded=True, gps_retained=bool(gps), gps_tags=sorted(gps))


class AuthorizationObservations(TestCase):
    setUp = fixtures.SecurityInputTests.setUp
    client_for = fixtures.SecurityInputTests.client_for

    def test_suspended_manager_configuration_access(self):
        client = self.client_for(self.manager)
        UserSuspension.objects.create(user=self.manager, reason='Audit global suspension')
        bootstrap = client.get('/api/event-admin/').status_code
        read = client.get('/api/event-admin/configuration/').status_code
        Event.objects.filter(pk=self.event.pk).update(state='DRAFT')
        write = client.put('/api/event-admin/configuration/', {'name': 'Audit change by suspended account'}, format='json').status_code
        self.event.refresh_from_db()
        observation('GLOBAL_SUSPENSION_MANAGEMENT', bootstrap=bootstrap, configuration_read=read,
            configuration_write=write, changed=self.event.name == 'Audit change by suspended account')

    def test_revoked_delegate_configuration_access(self):
        owner = EventAdministrator.objects.get(event=self.event, user=self.manager)
        target = EventAdministrator.objects.create(event=self.event, user=self.user, role='MODERATOR')
        owner.delegated_to = self.user
        owner.save()
        target.is_active = False
        target.save()
        client = self.client_for(self.user)
        bootstrap = client.get('/api/event-admin/').status_code
        read = client.get('/api/event-admin/configuration/').status_code
        Event.objects.filter(pk=self.event.pk).update(state='DRAFT')
        write = client.put('/api/event-admin/configuration/', {'name': 'Audit change by revoked delegate'}, format='json').status_code
        self.event.refresh_from_db()
        observation('REVOKED_DELEGATE_MANAGEMENT', bootstrap=bootstrap, configuration_read=read,
            configuration_write=write, changed=self.event.name == 'Audit change by revoked delegate')
