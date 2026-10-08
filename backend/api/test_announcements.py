from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.services import AuditUnavailable
from apps.events.models import Event, EventAdministrator
from apps.events.services import configure
from apps.notifications.announcements import dispatch_due
from apps.notifications.models import EventAnnouncement
from apps.organizations.models import Organization


class AnnouncementSchedulingTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.global_user = get_user_model().objects.create_user(username='global', is_superuser=True)
        self.manager = get_user_model().objects.create_user(username='manager')
        self.event = Event.objects.create(
            organization=Organization.objects.create(name='Cliente'), name='Evento', mode='ONLINE',
            starts_at=self.now + timedelta(days=1), ends_at=self.now + timedelta(days=1, hours=4),
        )
        EventAdministrator.objects.create(event=self.event, user=self.manager, role='ADMIN')
        self.client = APIClient()
        self.client.force_login(self.manager)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session.save()

    def post(self, action='schedule', **extra):
        return self.client.post('/api/event-admin/announcements/', {
            'title': 'Aviso', 'body': 'Mensagem', 'action': action,
            'scheduled': (self.event.starts_at + timedelta(hours=1)).isoformat(), **extra,
        }, format='json')

    def announcement(self, scheduled, state='SCHEDULED', **extra):
        return EventAnnouncement.objects.create(
            event=self.event, author=self.manager, title='Aviso', body='Mensagem',
            state=state, scheduled_at=scheduled, **extra,
        )

    def test_manager_can_create_and_edit_drafts_and_schedules_before_opening(self):
        for state in ['DRAFT', 'SCHEDULED']:
            with self.subTest(state=state):
                Event.objects.filter(pk=self.event.pk).update(state=state)
                draft = self.post('draft')
                self.assertEqual(draft.status_code, 200)
                self.assertEqual(draft.json()['state'], 'DRAFT')
                self.assertIsNone(draft.json()['scheduled'])
                scheduled = self.post(id=draft.json()['id'], title='Editado')
                self.assertEqual(scheduled.status_code, 200)
                self.assertEqual(scheduled.json()['state'], 'SCHEDULED')
                self.assertEqual(scheduled.json()['title'], 'Editado')
                self.assertEqual(self.post('send', confirmed=True).status_code, 403)

    def test_schedule_bounds_include_start_and_exclude_end(self):
        for value, expected in [
            (self.event.starts_at - timedelta(seconds=1), 400),
            (self.event.starts_at, 200),
            (self.event.ends_at - timedelta(seconds=1), 200),
            (self.event.ends_at, 400),
            (self.event.ends_at + timedelta(seconds=1), 400),
            (self.now - timedelta(seconds=1), 400),
        ]:
            with self.subTest(value=value):
                self.assertEqual(self.post(scheduled=value.isoformat(), confirmed=True).status_code, expected)

    def test_dates_required_for_scheduling_but_not_drafts(self):
        for field in ['starts_at', 'ends_at']:
            with self.subTest(field=field):
                Event.objects.filter(pk=self.event.pk).update(**{field: None})
                self.assertEqual(self.post().status_code, 400)
                self.assertEqual(self.post('draft').status_code, 200)
                Event.objects.filter(pk=self.event.pk).update(**{field: getattr(self.event, field)})

    def test_closed_and_archived_events_remain_read_only(self):
        for state in ['CLOSED', 'ARCHIVED']:
            Event.objects.filter(pk=self.event.pk).update(state=state)
            for action in ['draft', 'schedule', 'send']:
                self.assertEqual(self.post(action, confirmed=True).status_code, 403)

    def test_date_changes_reset_only_out_of_range_unsent_schedules(self):
        Event.objects.filter(pk=self.event.pk).update(state='SCHEDULED')
        early = self.announcement(self.event.starts_at)
        valid = self.announcement(self.event.starts_at + timedelta(hours=2))
        late = self.announcement(self.event.ends_at - timedelta(minutes=10))
        sent = self.announcement(self.event.starts_at, state='SENT', sent_at=self.now)
        other_event = Event.objects.create(organization=self.event.organization, name='Outro', mode='ONLINE')
        other = EventAnnouncement.objects.create(event=other_event, author=self.manager, title='Outro', body='Mensagem', state='SCHEDULED', scheduled_at=self.event.starts_at)
        self.client.force_login(self.global_user)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session.save()
        response = self.client.put('/api/event-admin/configuration/', {
            'starts_at': (self.event.starts_at + timedelta(hours=1)).isoformat(),
            'ends_at': (self.event.starts_at + timedelta(hours=3)).isoformat(), 'confirmed': True,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        for item in [early, late]:
            item.refresh_from_db()
            self.assertEqual(item.state, 'DRAFT')
            self.assertIsNone(item.scheduled_at)
        for item, expected in [(valid, 'SCHEDULED'), (sent, 'SENT'), (other, 'SCHEDULED')]:
            item.refresh_from_db()
            self.assertEqual(item.state, expected)

    def test_removing_a_date_resets_schedules_and_rollback_preserves_them(self):
        item = self.announcement(self.event.starts_at)
        with patch('apps.audit.services.AuditLog.objects.create', side_effect=RuntimeError('failure')):
            with self.assertRaises(AuditUnavailable):
                configure(self.event, self.global_user, {'starts_at': None})
        item.refresh_from_db()
        self.event.refresh_from_db()
        self.assertEqual(item.state, 'SCHEDULED')
        self.assertIsNotNone(self.event.starts_at)
        configure(self.event, self.global_user, {'starts_at': None})
        item.refresh_from_db()
        self.assertEqual(item.state, 'DRAFT')
        self.assertIsNone(item.scheduled_at)

    def test_due_notices_wait_until_event_is_open_without_interrupting_dispatch(self):
        for state in ['DRAFT', 'SCHEDULED']:
            Event.objects.filter(pk=self.event.pk).update(state=state)
            item = self.announcement(self.event.starts_at)
            dispatch_due(self.event.starts_at + timedelta(seconds=1))
            item.refresh_from_db()
            self.assertEqual(item.state, 'SCHEDULED')
            self.assertIsNone(item.sent_at)
