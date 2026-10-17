from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import signing
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.settings import api_settings
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from apps.audit.models import AuditLog
from apps.events.models import Event
from apps.interactions.models import Interaction
from apps.matches.models import Match
from apps.messaging.models import Conversation, Message
from apps.notifications.models import Notification
from apps.moderation.models import ModerationCase
from apps.reports.models import Report
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile


class ThrottlingTests(TestCase):
    def setUp(self):
        # Short budgets exercise the configured classes through actual endpoints.
        # Throttling stays enabled for the entire test suite.
        rates = patch.dict(SimpleRateThrottle.THROTTLE_RATES, {
            'anon': '6/min', 'user': '12/min', 'login': '3/min',
            'register': '2/min', 'messages': '2/min', 'interactions': '2/min', 'reports': '2/min',
        })
        rates.start()
        self.addCleanup(rates.stop)
        self.clock = patch.object(SimpleRateThrottle, 'timer', return_value=1000.0)
        self.timer = self.clock.start()
        self.addCleanup(self.clock.stop)
        self.event = Event.objects.create(
            organization=Organization.objects.create(name='Throttle client'),
            name='Throttle event', mode='ONLINE', state='RUNNING',
            ends_at=timezone.now() + timedelta(hours=2),
        )
        self.people = []
        for name in ['sender', 'recipient', 'another', 'untouched']:
            user = get_user_model().objects.create_user(username=f'throttle-{name}')
            participant = EventParticipant.objects.create(event=self.event, user=user, is_active=True)
            ParticipantProfile.objects.create(participant=participant, first_name=name, last_name='Test')
            self.people.append(participant)
        self.sender, self.recipient, self.another, self.untouched = self.people
        for peer in [self.recipient, self.another]:
            first, second = sorted([self.sender, peer], key=lambda p: p.pk.int)
            Conversation.objects.create(match=Match.objects.create(participant=first, partner=second))
        self.client = self.client_for(self.sender)

    def client_for(self, participant):
        client = APIClient()
        client.force_login(participant.user)
        session = client.session
        session['event_id'] = str(self.event.pk)
        session['navigation'] = 'participant'
        session.save()
        client.defaults['HTTP_X_EVENT_ID'] = session.get('event_id', '')
        return client

    def assert_throttled(self, response):
        self.assertEqual(response.status_code, 429, response.content)
        self.assertGreater(int(response['Retry-After']), 0)
        self.assertIn('detail', response.json())

    def test_defaults_include_global_and_scoped_limits(self):
        self.assertEqual(
            [cls.__name__ for cls in api_settings.DEFAULT_THROTTLE_CLASSES],
            ['AnonRateThrottle', 'UserRateThrottle', 'WriteScopedRateThrottle'],
        )
        for scope in ['anon', 'user', 'login', 'register', 'messages', 'interactions', 'reports']:
            self.assertIn(scope, api_settings.DEFAULT_THROTTLE_RATES)

    def test_anonymous_budget_is_per_ip_and_recovers_after_window(self):
        client = APIClient()
        for _ in range(6):
            self.assertEqual(client.get('/api/session/').status_code, 200)
        self.assert_throttled(APIClient().get('/api/session/'))
        self.assertEqual(client.get('/api/session/', REMOTE_ADDR='192.0.2.2').status_code, 200)
        self.timer.return_value += 61
        self.assertEqual(client.get('/api/session/').status_code, 200)

    def test_authenticated_budget_survives_new_session_and_ip_without_blocking_other_users(self):
        for _ in range(12):
            self.assertEqual(self.client.get('/api/session/').status_code, 200)
        another_session = self.client_for(self.sender)
        self.assert_throttled(another_session.get('/api/session/', REMOTE_ADDR='192.0.2.2'))
        other_user = self.client_for(self.recipient)
        self.assertEqual(other_user.get('/api/session/').status_code, 200)

    def test_login_attempts_count_failures_and_ignore_spoofed_forwarded_prefix(self):
        client = APIClient()
        with patch('api.views.authenticate', return_value=None) as authenticate:
            for index in range(3):
                response = client.post('/api/auth/login/', {
                    'email': f'attempt-{index}@example.com', 'password': 'Wrong-password-2026!',
                }, format='json', HTTP_X_FORWARDED_FOR=f'198.51.100.{index}, 192.0.2.5, 172.18.0.2')
                self.assertEqual(response.status_code, 400, response.content)
            response = APIClient().post('/api/auth/login/', {
                'email': 'another@example.com', 'password': 'Wrong-password-2026!',
            }, format='json', HTTP_X_FORWARDED_FOR='198.51.100.99, 192.0.2.5, 172.18.0.2')
            self.assert_throttled(response)
            self.assertEqual(authenticate.call_count, 3)
            response = client.post('/api/auth/login/', {
                'email': 'another@example.com', 'password': 'Wrong-password-2026!',
            }, format='json', HTTP_X_FORWARDED_FOR='192.0.2.6, 172.18.0.2')
            self.assertEqual(response.status_code, 400)
            self.timer.return_value += 61
            response = client.post('/api/auth/login/', {
                'email': 'another@example.com', 'password': 'Wrong-password-2026!',
            }, format='json', HTTP_X_FORWARDED_FOR='192.0.2.5, 172.18.0.2')
            self.assertEqual(response.status_code, 400)

    @override_settings(REST_FRAMEWORK={**api_settings.user_settings, 'NUM_PROXIES': 0})
    def test_direct_deployment_ignores_untrusted_forwarded_header(self):
        client = APIClient()
        for index in range(6):
            response = client.get('/api/session/', HTTP_X_FORWARDED_FOR=f'192.0.2.{index}')
            self.assertEqual(response.status_code, 200)
        self.assert_throttled(client.get('/api/session/', HTTP_X_FORWARDED_FOR='198.51.100.3'))

    def test_successful_login_does_not_bypass_ip_budget(self):
        user = get_user_model().objects.create_user(
            username='login@example.com', email='login@example.com',
            password='Strong-login-password-2026!', is_superuser=True,
        )
        client = APIClient()
        for _ in range(3):
            response = client.post('/api/auth/login/', {
                'email': user.email, 'password': 'Strong-login-password-2026!',
            }, format='json')
            self.assertEqual(response.status_code, 200, response.content)
        self.assert_throttled(client.post('/api/auth/login/', {
            'email': user.email, 'password': 'Strong-login-password-2026!',
        }, format='json'))

    def test_registration_budget_is_shared_by_sessions_and_blocks_creation(self):
        payload = {
            'password': 'Strong-registration-password-2026!',
            'invite': signing.dumps(str(self.event.pk), salt='event-join'),
        }
        for index in range(2):
            response = APIClient().post('/api/auth/register/', {
                **payload, 'email': f'new-{index}@example.com',
            }, format='json')
            self.assertEqual(response.status_code, 201, response.content)
        audit_count = AuditLog.objects.count()
        response = APIClient().post('/api/auth/register/', {
            **payload, 'email': 'blocked@example.com',
        }, format='json')
        self.assert_throttled(response)
        self.assertFalse(get_user_model().objects.filter(email='blocked@example.com').exists())
        self.assertEqual(AuditLog.objects.count(), audit_count)
        response = APIClient().post('/api/auth/register/', {
            **payload, 'email': 'allowed@example.com',
        }, format='json', REMOTE_ADDR='192.0.2.8')
        self.assertEqual(response.status_code, 201, response.content)

    def test_invalid_registration_attempts_also_consume_budget(self):
        client = APIClient()
        for _ in range(2):
            self.assertEqual(client.post('/api/auth/register/', {}, format='json').status_code, 403)
        self.assert_throttled(client.post('/api/auth/register/', {}, format='json'))

    def test_message_limit_spans_conversations_and_preserves_read_access(self):
        url = f'/api/conversations/{self.recipient.pk}/messages/'
        for _ in range(4):
            self.assertEqual(self.client.get(url).status_code, 200)
        for _ in range(2):
            response = self.client.post(url, {'text': 'Hello'}, format='json')
            self.assertEqual(response.status_code, 201, response.content)
        counts = (Message.objects.count(), AuditLog.objects.count(), Notification.objects.count())
        response = self.client.post(f'/api/conversations/{self.another.pk}/messages/', {'text': 'Spam'}, format='json')
        self.assert_throttled(response)
        self.assertEqual((Message.objects.count(), AuditLog.objects.count(), Notification.objects.count()), counts)
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client_for(self.recipient).post(
            f'/api/conversations/{self.sender.pk}/messages/', {'text': 'Reply'}, format='json',
        )
        self.assertEqual(response.status_code, 201, response.content)

    def test_interaction_budget_spans_targets_and_is_independent_from_messages(self):
        for peer in [self.recipient, self.another]:
            response = self.client.post(f'/api/interactions/{peer.pk}/', {'decision': 'LIKE'}, format='json')
            self.assertEqual(response.status_code, 200, response.content)
        counts = (Interaction.objects.count(), AuditLog.objects.count(), Notification.objects.count())
        response = self.client.post(f'/api/interactions/{self.untouched.pk}/', {'decision': 'LIKE'}, format='json')
        self.assert_throttled(response)
        self.assertEqual((Interaction.objects.count(), AuditLog.objects.count(), Notification.objects.count()), counts)
        response = self.client.post(f'/api/conversations/{self.recipient.pk}/messages/', {'text': 'Hello'}, format='json')
        self.assertEqual(response.status_code, 201, response.content)

    def test_scoped_limits_do_not_replace_global_budget(self):
        with patch.dict(SimpleRateThrottle.THROTTLE_RATES, {'user': '2/min', 'messages': '5/min'}):
            url = f'/api/conversations/{self.recipient.pk}/messages/'
            for _ in range(2):
                self.assertEqual(self.client.post(url, {'text': 'Hello'}, format='json').status_code, 201)
            self.assert_throttled(self.client.post(url, {'text': 'Spam'}, format='json'))
            self.assertEqual(Message.objects.count(), 2)

    def test_report_limit_spans_targets_sessions_and_ips_without_side_effects(self):
        payload = {'reasons': ['Outro'], 'description': 'Please review this participant.'}
        for target in [self.recipient, self.another]:
            response = self.client.post(f'/api/reports/{target.pk}/', payload, format='json')
            self.assertEqual(response.status_code, 201, response.content)
        before = (Report.objects.count(), ModerationCase.objects.count(), AuditLog.objects.count())
        other_session = self.client_for(self.sender)
        self.assert_throttled(other_session.post(f'/api/reports/{self.untouched.pk}/', payload,
                                               format='json', REMOTE_ADDR='192.0.2.9'))
        self.assertEqual((Report.objects.count(), ModerationCase.objects.count(), AuditLog.objects.count()), before)
        self.assertEqual(self.client.get('/api/reports/').status_code, 200)
        self.assertEqual(self.client_for(self.recipient).post(f'/api/reports/{self.untouched.pk}/', payload,
                                                          format='json').status_code, 201)
        self.timer.return_value += 61
        self.assertEqual(self.client.post(f'/api/reports/{self.untouched.pk}/', payload, format='json').status_code, 201)

    def test_invalid_and_duplicate_report_attempts_consume_the_write_budget(self):
        url = f'/api/reports/{self.recipient.pk}/'
        payload = {'reasons': ['Outro'], 'description': 'Please review this participant.'}
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 201)
        self.assertEqual(self.client.post(url, payload, format='json').status_code, 400)
        self.assert_throttled(self.client.post(f'/api/reports/{self.another.pk}/', {}, format='json'))
        self.assertEqual(Report.objects.count(), 1)
        self.timer.return_value += 61
        self.assertEqual(self.client.post(url, {}, format='json').status_code, 400)
        self.assertEqual(self.client.post(f'/api/reports/{self.another.pk}/', {}, format='json').status_code, 400)
        self.assert_throttled(self.client.post(f'/api/reports/{self.untouched.pk}/', payload, format='json'))
