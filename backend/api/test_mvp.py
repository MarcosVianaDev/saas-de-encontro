from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from apps.audit.models import AuditLog
from apps.audit.services import AuditUnavailable
from apps.events.models import Event, EventAdministrator
from apps.events.services import transition, synchronize
from apps.events.tasks import synchronize_events
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.moderation.models import EventSuspension, EventBan
from apps.notifications.models import Notification


class FoundationTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.owner = get_user_model().objects.create_user(username='global', is_superuser=True)
        self.org = Organization.objects.create(name='Cliente fictício')
        self.event = Event.objects.create(organization=self.org, name='Evento fictício', responsible=self.owner,
            starts_at=self.now+timedelta(minutes=30), ends_at=self.now+timedelta(hours=2))
        self.client = APIClient(); self.client.force_login(self.owner)
        session = self.client.session; session['event_id'] = str(self.event.pk); session.save()

    def test_transition_retries_do_not_duplicate_audit_or_notifications(self):
        transition(self.event, 'SCHEDULED', actor=self.owner)
        transition(self.event, 'OPEN', actor=self.owner)
        count = (AuditLog.objects.count(), Notification.objects.count())
        transition(self.event, 'OPEN', actor=self.owner)
        self.assertEqual(count, (AuditLog.objects.count(), Notification.objects.count()))
        with self.assertRaises(ValidationError): transition(self.event, 'RUNNING', actor=self.owner)
        event = transition(self.event, 'RUNNING', actor=self.owner, now=self.now+timedelta(minutes=30))
        self.assertEqual(event.state, 'RUNNING')

    def test_celery_calls_same_service_and_observes_automatic_delay(self):
        transition(self.event, 'SCHEDULED', actor=self.owner)
        with patch('apps.events.tasks.synchronize', return_value=2) as service:
            self.assertEqual(synchronize_events.run(), 2); service.assert_called_once()
        synchronize(self.now+timedelta(minutes=26))
        self.event.refresh_from_db(); self.assertEqual(self.event.state, 'OPEN')
        synchronize(self.now+timedelta(minutes=30))
        self.event.refresh_from_db(); self.assertEqual(self.event.state, 'OPEN')
        synchronize(self.now+timedelta(minutes=40))
        self.event.refresh_from_db(); self.assertEqual(self.event.state, 'RUNNING')
        transition(self.event, 'PAUSED', actor=self.owner)
        synchronize(self.now+timedelta(hours=2))
        self.event.refresh_from_db(); self.assertEqual(self.event.state, 'CLOSED')
        synchronize(self.now+timedelta(hours=2, days=15))
        self.event.refresh_from_db(); self.assertEqual(self.event.state, 'ARCHIVED')

    def test_audit_failure_rolls_back_domain_changes(self):
        with patch('apps.audit.services.AuditLog.objects.create', side_effect=RuntimeError('failure')):
            with self.assertRaises(AuditUnavailable): transition(self.event, 'SCHEDULED', actor=self.owner)
        self.event.refresh_from_db(); self.assertEqual(self.event.state, 'DRAFT')
        self.assertFalse(Notification.objects.exists())

    def test_early_closing_requires_confirmation_reason_and_session_challenge(self):
        transition(self.event, 'SCHEDULED', actor=self.owner); transition(self.event, 'OPEN', actor=self.owner)
        endpoint = '/api/event-admin/transition/'
        self.assertEqual(self.client.post(endpoint, {'state':'CLOSED'}, format='json').status_code, 400)
        self.client.get(endpoint)
        answer = self.client.session['closing_challenge']['answer']
        result = self.client.post(endpoint, {'state':'CLOSED','confirmed':True,'reason':'Cancelamento operacional','captcha':answer}, format='json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['state'], 'CLOSED')
        self.assertEqual(self.client.post(endpoint, {'state':'RUNNING'}, format='json').status_code, 400)

    def test_progressive_configuration_and_authorization(self):
        url = '/api/event-admin/configuration/'
        self.assertEqual(self.client.put(url, {'radius_m':2000},format='json').status_code,200)
        transition(self.event,'SCHEDULED',actor=self.owner)
        self.assertEqual(self.client.put(url, {'name':'Outro'},format='json').status_code,400)
        self.assertEqual(self.client.put(url, {'name':'Outro','confirmed':True},format='json').status_code,200)
        transition(self.event,'OPEN',actor=self.owner)
        self.assertEqual(self.client.put(url, {'name':'Bloqueado'},format='json').status_code,403)
        self.assertEqual(self.client.put(url, {'radius_m':1800},format='json').status_code,200)
        transition(self.event,'RUNNING',actor=self.owner,now=self.now+timedelta(minutes=30))
        self.assertEqual(self.client.put(url, {'radius_m':1700},format='json').status_code,403)

    def test_participation_presence_and_sanction_are_independent(self):
        user = get_user_model().objects.create_user(username='participant')
        p = EventParticipant.objects.create(user=user,event=self.event,is_active=True,presence='OUTSIDE')
        self.assertEqual(p.operational_status,'Ativo')
        EventSuspension.objects.create(participant=p,actor=self.owner,reason='Análise')
        self.assertEqual(p.operational_status,'Suspenso')
        self.assertEqual(p.presence,'OUTSIDE')
        self.assertTrue(p.user.is_active)
        EventBan.objects.create(participant=p,reason='Decisão')
        self.assertEqual(p.operational_status,'Banido')
        from apps.moderation.models import UserSuspension
        UserSuspension.objects.create(user=user,reason='Restrição global')
        self.assertEqual(p.operational_status,'Conta suspensa')
