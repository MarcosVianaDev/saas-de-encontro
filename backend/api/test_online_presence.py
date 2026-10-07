from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from apps.events.models import Event, EventAdministrator
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.participants.location import reading, failed, exception, expire_exceptions, synchronize_online_presence
from apps.profiles.models import ParticipantProfile
from .services import bootstrap, person_payload
from .event_admin import participant_payload


class OnlinePresenceTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.user = get_user_model().objects.create_user(username='online', email='online@example.com')
        self.manager = get_user_model().objects.create_user(username='manager')
        self.event = Event.objects.create(organization=Organization.objects.create(name='Online'),
            name='Online', mode='ONLINE', state='RUNNING', location_interval_minutes=10)
        EventAdministrator.objects.create(event=self.event, user=self.manager)
        self.participant = EventParticipant.objects.create(event=self.event, user=self.user,
            is_active=True, registration_status='ACTIVE', activated_at=self.now, last_seen_at=self.now)
        ParticipantProfile.objects.create(participant=self.participant, first_name='Online', last_name='Person')
        self.client = APIClient()
        self.login(self.user)

    def login(self, user):
        self.client.force_login(user)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session['navigation'] = 'participant' if user == self.user else 'administration'
        session.save()

    def test_presence_uses_configured_interval_and_exact_boundary(self):
        for minutes in [1, 10, 30]:
            self.event.location_interval_minutes = minutes
            self.event.save()
            self.participant.event = self.event
            for elapsed, expected in [(minutes * 60, 'PRESENT'), (minutes * 60 + 1, 'ABSENT')]:
                self.participant.last_seen_at = self.now - timedelta(seconds=elapsed)
                with patch('django.utils.timezone.now', return_value=self.now):
                    self.assertEqual(bootstrap(self.participant)['presence'], expected)
                    self.assertEqual(person_payload(self.participant)['online'], expected == 'PRESENT')
                    self.assertEqual(participant_payload(self.participant, False)['online'], expected == 'PRESENT')
            self.participant.last_seen_at = None
            self.assertEqual(self.participant.current_presence, 'ABSENT')

    def test_inactivity_and_return_preserve_activation(self):
        EventParticipant.objects.filter(pk=self.participant.pk).update(last_seen_at=self.now-timedelta(minutes=11))
        self.assertEqual(synchronize_online_presence(self.now), 1)
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.presence, 'ABSENT')
        self.assertTrue(self.participant.is_active)
        response = self.client.get('/api/bootstrap/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['presence'], 'PRESENT')
        self.assertTrue(response.json()['socialAvailable'])
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.presence, 'PRESENT')
        first_contact = self.participant.last_seen_at
        with patch('django.utils.timezone.now', return_value=first_contact+timedelta(seconds=5)):
            self.client.get('/api/bootstrap/')
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.last_seen_at, first_contact+timedelta(seconds=5))

    def test_online_ignores_gps_and_stale_retry_state(self):
        EventParticipant.objects.filter(pk=self.participant.pk).update(location_failure_started_at=self.now,
            location_retry_count=5, location_retry_exhausted_at=self.now,
            location_next_due_at=self.now-timedelta(minutes=1), location_exception_until=self.now-timedelta(minutes=1))
        reading(self.participant, {})
        failed(self.participant, 'invalid', self.now)
        self.assertEqual(expire_exceptions(self.now), 0)
        self.assertFalse(self.participant.location_readings.exists())
        self.assertFalse(self.participant.location_anomalies.exists())
        with self.assertRaises(ValidationError):
            exception(self.participant, self.manager, 10, 'GPS', self.now)
        for body in [{'action': 'deny'}, {'action': 'failed'}, {'latitude': 'invalid'}]:
            response = self.client.post('/api/location/', body, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()['active'])
            self.assertFalse(response.json()['location']['failed'])

    def test_admin_activity_uses_event_interval(self):
        self.login(self.manager)
        EventParticipant.objects.filter(pk=self.participant.pk).update(last_seen_at=self.now-timedelta(minutes=6))
        response = self.client.get('/api/event-admin/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['metrics']['active'], 1)
        EventParticipant.objects.filter(pk=self.participant.pk).update(last_seen_at=self.now-timedelta(minutes=11))
        response = self.client.get('/api/event-admin/')
        self.assertEqual(response.json()['metrics']['active'], 0)
        self.assertEqual(response.json()['participants'][0]['presence'], 'ABSENT')

    def test_physical_presence_and_gps_validation_are_preserved(self):
        self.event.mode = 'PHYSICAL'
        self.event.save()
        self.participant.event = self.event
        self.participant.presence = 'OUTSIDE'
        self.participant.last_seen_at = self.now-timedelta(minutes=6)
        self.assertEqual(self.participant.current_presence, 'OUTSIDE')
        self.assertFalse(self.participant.activity_is_recent(self.now))
        with self.assertRaises(ValidationError):
            reading(self.participant, {})
        self.assertEqual(synchronize_online_presence(self.now), 0)
