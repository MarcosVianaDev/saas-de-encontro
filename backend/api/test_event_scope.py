import tempfile
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.events.models import Event, EventAdministrator, ExportJob
from apps.notifications.models import Notification
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantPhoto, ParticipantProfile


class EventScopeTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.manager = users.objects.create_user(username='scope-manager')
        self.global_user = users.objects.create_user(username='scope-global', is_superuser=True)
        self.org = Organization.objects.create(name='Scope client')
        self.first = Event.objects.create(organization=self.org, name='First', mode='ONLINE')
        self.second = Event.objects.create(organization=self.org, name='Second', mode='ONLINE')
        self.foreign = Event.objects.create(organization=Organization.objects.create(name='Other client'), name='Foreign', mode='ONLINE')
        for event in [self.first, self.second]:
            EventAdministrator.objects.create(event=event, user=self.manager, role='ADMIN')
        self.person = EventParticipant.objects.create(
            event=self.second, user=users.objects.create_user(username='scope-person'), is_active=True,
        )
        ParticipantProfile.objects.create(participant=self.person, first_name='Test', last_name='Person')
        self.client = APIClient()
        self.client.force_login(self.manager)
        self.set_session(self.second)

    def set_session(self, event, navigation='administration'):
        session = self.client.session
        session['event_id'] = str(event.pk)
        session['navigation'] = navigation
        session.save()

    def headers(self, event=None, context='administration'):
        return {'HTTP_X_EVENT_ID': str((event or self.first).pk), 'HTTP_X_APP_CONTEXT': context}

    def test_administrative_endpoints_require_explicit_event_even_with_valid_session(self):
        self.client.force_login(self.global_user)
        self.set_session(self.second)
        paths = [
            'event-admin/', 'event-admin/configuration/', 'event-admin/transition/',
            'event-admin/team/', 'event-admin/passes/', 'event-admin/announcements/',
            'event-admin/support/', 'event-admin/financial/', 'event-admin/exports/',
            f'event-admin/participants/{self.person.pk}/profile/',
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get('/api/' + path)
                self.assertEqual(response.status_code, 400, response.content)
        for path, method, payload in [
            ('event-admin/configuration/', 'put', {'name': 'Must not change'}),
            ('event-admin/transition/', 'post', {'state': 'PAUSED', 'confirmed': True}),
            ('event-admin/team/', 'post', {'action': 'reclaim'}),
            ('event-admin/exports/', 'post', {}),
        ]:
            response = getattr(self.client, method)('/api/' + path, payload, format='json')
            self.assertEqual(response.status_code, 400, response.content)
        self.second.refresh_from_db()
        self.assertEqual(self.second.name, 'Second')
        self.assertEqual(self.second.state, 'DRAFT')
        self.assertFalse(ExportJob.objects.exists())
        self.assertFalse(AuditLog.objects.exists())

    def test_two_tabs_sharing_one_session_keep_writes_in_their_explicit_events(self):
        other_tab = APIClient()
        other_tab.cookies = self.client.cookies.copy()
        response = other_tab.post('/api/event-admin/', {'event': str(self.second.pk)}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        response = self.client.put('/api/event-admin/configuration/', {'name': 'First updated'}, format='json', **self.headers())
        self.assertEqual(response.status_code, 200, response.content)
        response = other_tab.put('/api/event-admin/configuration/', {'name': 'Second updated'}, format='json', **self.headers(self.second))
        self.assertEqual(response.status_code, 200, response.content)
        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertEqual(self.first.name, 'First updated')
        self.assertEqual(self.second.name, 'Second updated')
        self.assertEqual(self.client.session['event_id'], str(self.second.pk))
        self.assertEqual(
            set(AuditLog.objects.filter(action='event.configuration').values_list('object_id', flat=True)),
            {self.first.pk, self.second.pk},
        )

    def test_url_scope_works_without_session_event_and_rejects_header_conflict(self):
        session = self.client.session
        session.pop('event_id')
        session.save()
        url = f'/api/events/{self.first.pk}/event-admin/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['event']['id'], str(self.first.pk))
        self.assertEqual(self.client.get(url, **self.headers()).status_code, 200)
        self.assertEqual(self.client.get(url, **self.headers(self.second)).status_code, 400)

    def test_invalid_or_unknown_event_never_falls_back_to_session(self):
        for value, status in [('', 400), ('invalid', 400), (str(uuid4()), 404)]:
            with self.subTest(value=value):
                self.assertEqual(self.client.get('/api/event-admin/', HTTP_X_EVENT_ID=value).status_code, status)

    def test_explicit_event_does_not_grant_membership_or_ignore_revocation(self):
        self.assertEqual(self.client.get('/api/event-admin/', **self.headers(self.foreign)).status_code, 404)
        self.assertEqual(self.client.put('/api/event-admin/configuration/', {'name': 'No'}, format='json', **self.headers(self.foreign)).status_code, 403)
        EventAdministrator.objects.filter(user=self.manager, event=self.first).update(is_active=False)
        self.assertEqual(self.client.get('/api/event-admin/', **self.headers()).status_code, 404)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.name, 'Foreign')

    def test_roles_and_object_ids_are_checked_within_explicit_scope(self):
        EventAdministrator.objects.filter(user=self.manager, event=self.first).update(role='OPERATOR')
        self.assertEqual(self.client.get('/api/event-admin/team/', **self.headers()).status_code, 403)
        self.assertEqual(self.client.get(f'/api/event-admin/participants/{self.person.pk}/profile/', **self.headers()).status_code, 404)
        self.assertEqual(self.client.get(f'/api/event-admin/participants/{self.person.pk}/profile/', **self.headers(self.second)).status_code, 200)

    def test_team_reclaim_uses_explicit_event(self):
        delegate = get_user_model().objects.create_user(username='scope-delegate')
        EventAdministrator.objects.filter(user=self.manager).update(delegated_to=delegate)
        response = self.client.post('/api/event-admin/team/', {'action': 'reclaim'}, format='json', **self.headers())
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIsNone(EventAdministrator.objects.get(user=self.manager, event=self.first).delegated_to_id)
        self.assertEqual(EventAdministrator.objects.get(user=self.manager, event=self.second).delegated_to_id, delegate.pk)

    def test_notifications_respect_tab_context_and_event(self):
        first = Notification.objects.create(recipient=self.manager, event=self.first, title='First')
        second = Notification.objects.create(recipient=self.manager, event=self.second, title='Second')
        response = self.client.get('/api/notifications/', **self.headers())
        self.assertEqual([item['id'] for item in response.json()['items']], [str(first.pk)])
        response = self.client.post('/api/notifications/', {'id': str(second.pk)}, format='json', **self.headers())
        self.assertEqual(response.status_code, 404)
        second.refresh_from_db()
        self.assertIsNone(second.read_at)

    def test_bootstrap_restores_tab_context_instead_of_another_tabs_session(self):
        self.client.force_login(self.global_user)
        self.set_session(self.second, navigation='global')
        response = self.client.get('/api/bootstrap/', **self.headers())
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['navigation'], 'administration')
        self.assertEqual(response.json()['eventId'], str(self.first.pk))
        self.set_session(self.second)
        self.assertEqual(self.client.get('/api/bootstrap/', HTTP_X_APP_CONTEXT='global').json()['navigation'], 'global')
        self.assertEqual(self.client.get('/api/bootstrap/', HTTP_X_APP_CONTEXT='invalid').status_code, 400)

    def test_selection_response_identifies_new_event_even_with_previous_header(self):
        response = self.client.post('/api/event-admin/', {'event': str(self.second.pk)}, format='json', **self.headers())
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['eventId'], str(self.second.pk))
        self.client.force_login(self.global_user)
        response = self.client.post('/api/global/event/', {'event': str(self.first.pk)}, format='json')
        self.assertEqual(response.json()['eventId'], str(self.first.pk))

    def test_participant_context_and_event_are_independent_from_administrative_session(self):
        for event in [self.first, self.second]:
            participant = EventParticipant.objects.create(event=event, user=self.manager)
            ParticipantProfile.objects.create(participant=participant, first_name='Manager', last_name='Participant')
        response = self.client.get('/api/bootstrap/', **self.headers(context='participant'))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['navigation'], 'participant')
        self.assertEqual(response.json()['event']['id'], str(self.first.pk))

    def test_context_header_does_not_grant_global_administration(self):
        response = self.client.get('/api/bootstrap/', HTTP_X_APP_CONTEXT='global')
        self.assertEqual(response.status_code, 403)

    def test_export_reads_and_writes_use_explicit_scope(self):
        self.client.force_login(self.global_user)
        self.set_session(self.second)
        with patch('apps.events.export_tasks.generate.delay'), self.captureOnCommitCallbacks(execute=True):
            response = self.client.post('/api/event-admin/exports/', {}, format='json', **self.headers())
        self.assertEqual(response.status_code, 202, response.content)
        job = ExportJob.objects.get(pk=response.json()['id'])
        self.assertEqual(job.event_id, self.first.pk)
        self.assertEqual(self.client.get('/api/event-admin/exports/', **self.headers()).json()['id'], str(job.pk))
        self.assertEqual(self.client.get(f'/api/event-admin/exports/{job.pk}/', **self.headers(self.second)).status_code, 404)

    def test_private_photo_url_retains_event_after_session_switch(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            Path(directory, 'scope.jpg').write_bytes(b'private photo')
            photo = ParticipantPhoto.objects.create(participant=self.person, storage_key='scope.jpg', is_primary=True)
            response = self.client.get(f'/api/events/{self.second.pk}/event-admin/participants/{self.person.pk}/profile/')
            self.assertEqual(response.status_code, 200, response.content)
            url = response.json()['image']
            self.assertIn(str(self.second.pk), url)
            self.set_session(self.first)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'private photo')
            self.assertEqual(self.client.get(f'/api/events/{self.first.pk}/event-admin/photos/{photo.pk}/content/').status_code, 404)
