from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.events.models import Event, EventAdministrator
from apps.events.services import transition
from apps.organizations.models import Organization


class EventTimelineTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.user = get_user_model().objects.create_user(username='manager')
        self.event = Event.objects.create(
            organization=Organization.objects.create(name='Cliente'), name='Evento', mode='ONLINE',
            starts_at=self.now, ends_at=self.now + timedelta(hours=4),
        )
        EventAdministrator.objects.create(event=self.event, user=self.user, role='ADMIN')
        self.client = APIClient()
        self.client.force_login(self.user)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session['navigation'] = 'administration'
        session.save()

    def timeline(self):
        response = self.client.get('/api/event-admin/transition/')
        self.assertEqual(response.status_code, 200)
        return {item['state']: item for item in response.json()['timeline']}

    def test_hidden_states_and_unvisited_statuses(self):
        timeline = self.timeline()
        self.assertEqual(list(timeline), ['SCHEDULED', 'OPEN', 'RUNNING', 'PAUSED', 'CLOSED'])
        self.assertTrue(all(item['enteredAt'] is None for item in timeline.values()))

    def test_real_transition_times_and_latest_reentry(self):
        states = ['SCHEDULED', 'OPEN', 'RUNNING', 'PAUSED', 'RUNNING', 'PAUSED']
        expected = {}
        for index, state in enumerate(states):
            timestamp = self.now + timedelta(minutes=index)
            self.event = transition(self.event, state, actor=self.user, now=timestamp)
            expected[state] = timestamp.isoformat()
        other = Event.objects.create(organization=self.event.organization, name='Outro', mode='ONLINE')
        AuditLog.objects.create(action='event.transition', object_label=other._meta.label, object_id=other.pk,
                                details={'state': 'CLOSED', 'timestamp': self.now.isoformat()})
        timeline = self.timeline()
        for state, timestamp in expected.items():
            self.assertEqual(timeline[state]['enteredAt'], timestamp)
        self.assertIsNone(timeline['CLOSED']['enteredAt'])

    def test_legacy_event_uses_recorded_open_and_close_times(self):
        Event.objects.filter(pk=self.event.pk).update(opened_at=self.now, closed_at=self.now + timedelta(hours=1))
        timeline = self.timeline()
        self.assertEqual(timeline['OPEN']['enteredAt'], self.now.isoformat().replace('+00:00', 'Z'))
        self.assertEqual(timeline['CLOSED']['enteredAt'], (self.now + timedelta(hours=1)).isoformat().replace('+00:00', 'Z'))
