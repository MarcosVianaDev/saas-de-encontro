from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.events.models import Event, EventAdministrator
from apps.events.services import synchronize, transition
from apps.notifications.models import Notification
from apps.organizations.models import Organization


class EventRequestTests(TestCase):
    def setUp(self):
        self.manager = get_user_model().objects.create_user(username='manager', email='manager@example.com')
        self.global_user = get_user_model().objects.create_superuser(username='global', email='global@example.com', password='Global-password-2026!')
        self.org = Organization.objects.create(name='Client')
        self.source = Event.objects.create(organization=self.org, name='Existing event', mode='ONLINE', state='CLOSED')
        EventAdministrator.objects.create(event=self.source, user=self.manager)
        self.client = APIClient()
        self.login(self.manager)
        now = timezone.now()
        self.payload = {'event': 'Requested event', 'description': 'Description', 'mode': 'ONLINE',
            'starts': (now+timedelta(days=1)).isoformat(), 'ends': (now+timedelta(days=2)).isoformat(),
            'location_interval_minutes': 20, 'auto_activate_participants': True}

    def login(self, user, event=None):
        self.client.force_login(user)
        session = self.client.session
        session['event_id'] = str((event or self.source).pk)
        session['navigation'] = 'administration'
        session.save()

    def request_event(self, payload=None):
        response = self.client.post('/api/event-admin/requests/', payload or self.payload, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        return Event.objects.get(pk=response.json()['id'])

    def test_request_saves_draft_with_organization_owner_fields_and_notification(self):
        event = self.request_event()
        self.assertEqual(event.state, 'DRAFT')
        self.assertEqual(event.organization, self.org)
        self.assertEqual(event.responsible, self.manager)
        self.assertEqual(event.requested_by, self.manager)
        self.assertEqual(event.description, 'Description')
        self.assertEqual(event.location_interval_minutes, 20)
        self.assertTrue(event.auto_activate_participants)
        self.assertTrue(EventAdministrator.objects.filter(event=event, user=self.manager, role='ADMIN').exists())
        self.assertTrue(AuditLog.objects.filter(action='event.requested', object_id=event.pk).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.global_user, event=event).exists())
        synchronize(timezone.now()+timedelta(days=1))
        event.refresh_from_db()
        self.assertEqual(event.state, 'DRAFT')
        self.assertEqual(self.client.session['event_id'], str(self.source.pk))

    def test_requester_can_edit_draft_but_cannot_approve(self):
        event = self.request_event()
        self.login(self.manager, event)
        response = self.client.get('/api/event-admin/transition/')
        self.assertTrue(response.json()['pendingApproval'])
        self.assertNotIn('SCHEDULED', response.json()['actions'])
        response = self.client.put('/api/event-admin/configuration/', {
            'name': 'Updated', 'starts_at': (timezone.now()+timedelta(hours=2)).isoformat(),
            'settings': {'auto_activate_participants': False},
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.client.post('/api/event-admin/transition/', {'state': 'SCHEDULED'}, format='json').status_code, 403)
        with self.assertRaises(PermissionDenied):
            transition(event, 'SCHEDULED', automatic=True)
        event.refresh_from_db()
        self.assertEqual(event.state, 'DRAFT')

    def test_global_user_reviews_and_approves_requested_event_once(self):
        event = self.request_event()
        self.login(self.global_user, event)
        data = self.client.get('/api/event-admin/transition/').json()
        self.assertIn('SCHEDULED', data['actions'])
        for _ in range(2):
            response = self.client.post('/api/event-admin/transition/', {'state': 'SCHEDULED'}, format='json')
            self.assertEqual(response.status_code, 200, response.content)
            self.assertFalse(response.json()['pendingApproval'])
        event.refresh_from_db()
        self.assertEqual(event.state, 'SCHEDULED')
        self.assertEqual(AuditLog.objects.filter(action='event.approved', object_id=event.pk).count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.manager, event=event, title='Solicitação de evento aprovada').count(), 1)
        self.login(self.manager, event)
        response = self.client.put('/api/event-admin/configuration/', {'starts_at': self.payload['starts'], 'confirmed': True}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_only_event_managers_can_request(self):
        for role in ['MODERATOR', 'OPERATOR']:
            EventAdministrator.objects.filter(event=self.source, user=self.manager).update(role=role)
            self.assertEqual(self.client.post('/api/event-admin/requests/', self.payload, format='json').status_code, 403)
        outsider = get_user_model().objects.create_user(username='outsider')
        self.login(outsider)
        self.assertEqual(self.client.post('/api/event-admin/requests/', self.payload, format='json').status_code, 403)

    def test_request_cannot_override_state_owner_or_organization(self):
        for key, value in [('state', 'SCHEDULED'), ('client', str(self.org.pk)), ('requested_by', None), ('responsible', self.global_user.email)]:
            response = self.client.post('/api/event-admin/requests/', {**self.payload, key: value}, format='json')
            self.assertEqual(response.status_code, 400)
        self.assertEqual(Event.objects.count(), 1)

    def test_physical_request_validates_and_stores_location(self):
        physical = {**self.payload, 'mode': 'PHYSICAL', 'auto_activate_participants': False}
        self.assertEqual(self.client.post('/api/event-admin/requests/', physical, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/event-admin/requests/', {**self.payload, 'ends': self.payload['starts']}, format='json').status_code, 400)
        event = self.request_event({**physical, 'latitude': -23, 'longitude': -46, 'radius_m': 200, 'tolerance_m': 500})
        self.assertEqual(event.radius_m, 200)
        self.assertEqual(event.tolerance_m, 500)
        self.assertEqual(float(event.latitude), -23)

    def test_global_metrics_include_all_drafts(self):
        self.request_event()
        Event.objects.create(organization=self.org, name='Other draft', mode='ONLINE')
        self.login(self.global_user)
        response = self.client.get('/api/global/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['metrics']['DRAFT'], 2)
        self.assertEqual(len([event for event in response.json()['events'] if event['state'] == 'DRAFT']), 2)

    def test_global_access_to_draft_opens_event_data_and_restores_destination(self):
        event = self.request_event()
        self.login(self.global_user)
        for state, page in [('DRAFT', 'event'), ('SCHEDULED', 'dashboard')]:
            Event.objects.filter(pk=event.pk).update(state=state)
            response = self.client.post('/api/global/event/', {'event': str(event.pk)}, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['initialPage'], page)
            self.assertEqual(self.client.get('/api/bootstrap/').json()['initialPage'], page)
