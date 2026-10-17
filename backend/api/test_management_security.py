from datetime import timedelta
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from api import test_security_inputs as fixtures
from apps.events.models import Event, EventAdministrator
from apps.events.permissions import effective_role
from apps.events.services import configure, is_manager, transition
from apps.moderation.models import UserSuspension
from common.security import account_allowed
from config.admin_site import login_retry_after


class ManagementRestrictionTests(TestCase):
    setUp = fixtures.SecurityInputTests.setUp
    client_for = fixtures.SecurityInputTests.client_for

    def draft(self):
        Event.objects.filter(pk=self.event.pk).update(state='DRAFT')
        self.event.refresh_from_db()

    def assert_no_management(self, client):
        self.draft()
        before = Event.objects.count()
        for path in ['configuration/', 'transition/']:
            self.assertEqual(client.get('/api/event-admin/' + path).status_code, 403)
        self.assertEqual(client.put('/api/event-admin/configuration/', {'name': 'Unauthorized write'}, format='json').status_code, 403)
        self.assertEqual(client.post('/api/event-admin/transition/', {'state': 'SCHEDULED'}, format='json').status_code, 403)
        self.assertEqual(client.post('/api/event-admin/requests/', {}, format='json').status_code, 403)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, 'Security audit')
        self.assertEqual(self.event.state, 'DRAFT')
        self.assertEqual(Event.objects.count(), before)

    def delegate(self):
        owner = EventAdministrator.objects.get(event=self.event, user=self.manager)
        target = EventAdministrator.objects.create(event=self.event, user=self.user, role='MODERATOR')
        owner.delegated_to = self.user
        owner.save()
        self.assertTrue(is_manager(self.user, self.event))
        return owner, target

    def test_global_suspension_blocks_existing_session_and_domain_writes(self):
        client = self.client_for(self.manager)
        UserSuspension.objects.create(user=self.manager, reason='Security restriction')
        self.assert_no_management(client)
        self.assertFalse(is_manager(self.manager, self.event))
        with self.assertRaises(PermissionDenied):
            configure(self.event, self.manager, {'name': 'Unauthorized write'})
        with self.assertRaises(PermissionDenied):
            transition(self.event, 'SCHEDULED', actor=self.manager)
        self.assertEqual(client.get('/api/frontend/authorize/?audience=event-manager').status_code, 403)

    def test_revoked_delegate_with_stale_database_pointer_is_denied(self):
        owner, target = self.delegate()
        EventAdministrator.objects.filter(pk=target.pk).update(is_active=False)
        owner.refresh_from_db()
        self.assertEqual(owner.delegated_to_id, self.user.pk)
        self.assert_no_management(self.client_for(self.user))
        self.assertFalse(is_manager(self.user, self.event))
        self.assertTrue(is_manager(self.manager, self.event))

    def test_saving_revocation_clears_delegation_and_reactivation_does_not_restore_it(self):
        owner, target = self.delegate()
        target.is_active = False
        target.save()
        owner.refresh_from_db()
        self.assertIsNone(owner.delegated_to_id)
        target.is_active = True
        target.save()
        self.assertEqual(effective_role(target), 'MODERATOR')
        self.assert_no_management(self.client_for(self.user))

    def test_inactive_or_suspended_delegation_origin_cannot_grant_admin(self):
        owner, target = self.delegate()
        EventAdministrator.objects.filter(pk=owner.pk).update(is_active=False)
        self.assertFalse(is_manager(self.user, self.event))
        self.assertEqual(effective_role(target), 'MODERATOR')
        EventAdministrator.objects.filter(pk=owner.pk).update(is_active=True)
        UserSuspension.objects.create(user=self.manager, reason='Suspended delegator')
        self.assert_no_management(self.client_for(self.user))

    def test_valid_delegate_and_expired_suspension_keep_legitimate_access(self):
        self.delegate()
        UserSuspension.objects.create(user=self.user, reason='Expired', ends_at=timezone.now()-timedelta(seconds=1))
        self.draft()
        response = self.client_for(self.user).put('/api/event-admin/configuration/', {'name': 'Authorized change'}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(is_manager(self.user, self.event))

    def test_suspended_global_account_cannot_use_global_api_admin_or_spa(self):
        admin = get_user_model().objects.create_user(username='restricted-admin', is_staff=True, is_superuser=True)
        client = self.client_for(admin)
        UserSuspension.objects.create(user=admin, reason='Global restriction')
        self.assertFalse(account_allowed(admin))
        self.assertEqual(client.get('/api/global/').status_code, 403)
        for audience in ['participant', 'event-manager', 'global']:
            self.assertEqual(client.get('/api/frontend/authorize/', {'audience': audience}).status_code, 403)
        self.assertEqual(client.get('/mcx/').status_code, 302)
        self.assertFalse(is_manager(admin, self.event))

    def test_suspended_login_does_not_create_session_and_logout_remains_available(self):
        UserSuspension.objects.create(user=self.user, reason='Global restriction')
        client = APIClient()
        response = client.post('/api/auth/login/', {'email': self.user.email, 'password': 'Audit-safe-password-2026!'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('_auth_user_id', client.session)
        existing = self.client_for(self.user)
        self.assertEqual(existing.post('/api/auth/logout/').status_code, 200)


@override_settings(ADMIN_LOGIN_IP_LIMIT=3, ADMIN_LOGIN_ACCOUNT_LIMIT=4, ADMIN_LOGIN_WINDOW_SECONDS=60)
class AdminLoginSecurityTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.get('/mcx/login/')
        self.token = self.client.cookies['csrftoken'].value
        clock = patch('config.admin_site.time.time', return_value=1200)
        clock.start()
        self.addCleanup(clock.stop)

    def attempt(self, username='invalid@example.invalid', forwarded='192.0.2.1, 172.18.0.1', client=None, token=None, **extra):
        return (client or self.client).post('/mcx/login/', {'username': username, 'password': 'Invalid-password-2026!'},
            HTTP_X_CSRFTOKEN=token or self.token, HTTP_X_FORWARDED_FOR=forwarded, **extra)

    def test_new_path_and_old_path_removed(self):
        self.assertEqual(reverse('admin:index'), '/mcx/')
        self.assertEqual(self.client.get('/admin/').status_code, 404)
        self.assertEqual(self.client.get('/admin/login/').status_code, 404)
        self.assertEqual(self.client.get('/mcx/login/').status_code, 200)

    def test_ip_limit_survives_sessions_usernames_and_spoofed_prefix(self):
        for index in range(3):
            self.assertEqual(self.attempt(username=f'name-{index}', forwarded=f'198.51.100.{index}, 192.0.2.1, 172.18.0.1').status_code, 200)
        other = Client(enforce_csrf_checks=True)
        other.get('/mcx/login/')
        response = self.attempt(client=other, token=other.cookies['csrftoken'].value, forwarded='198.51.100.99, 192.0.2.1, 172.18.0.1')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Retry-After'], '60')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.attempt(forwarded='192.0.2.2, 172.18.0.1').status_code, 200)

    def test_account_limit_survives_ip_rotation_and_case_changes(self):
        for index in range(4):
            self.assertEqual(self.attempt(username='TARGET@example.invalid', forwarded=f'192.0.2.{index+2}, 172.18.0.1').status_code, 200)
        response = self.attempt(username='target@EXAMPLE.INVALID', forwarded='192.0.2.10, 172.18.0.1')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(self.attempt(username='other-account', forwarded='192.0.2.11, 172.18.0.1').status_code, 200)

    def test_unicode_equivalent_usernames_share_the_account_budget(self):
        for index in range(4):
            self.assertEqual(self.attempt(username='admin', forwarded=f'192.0.2.{index+2}, 172.18.0.1').status_code, 200)
        self.assertEqual(self.attempt(username='ａｄｍｉｎ', forwarded='192.0.2.10, 172.18.0.1').status_code, 429)

    def test_blocked_ip_cannot_exhaust_another_accounts_budget(self):
        for _ in range(3):
            self.assertEqual(self.attempt(username='other-account').status_code, 200)
        for _ in range(4):
            self.assertEqual(self.attempt(username='protected-account').status_code, 429)
        for index in range(4):
            self.assertEqual(self.attempt(username='protected-account', forwarded=f'192.0.2.{index+2}, 172.18.0.1').status_code, 200)

    def test_concurrent_requests_cannot_exceed_the_atomic_ip_budget(self):
        def attempt(_):
            request = RequestFactory().post('/mcx/login/', {'username': 'atomic-budget'})
            return login_retry_after(request)
        with ThreadPoolExecutor(max_workers=12) as executor:
            waits = list(executor.map(attempt, range(12)))
        self.assertLessEqual(waits.count(0), 3)
        self.assertTrue(any(waits))

    def test_budget_recovers_after_window(self):
        for _ in range(3):
            self.attempt()
        self.assertEqual(self.attempt().status_code, 429)
        with patch('config.admin_site.time.time', return_value=1261):
            self.assertEqual(self.attempt().status_code, 200)

    def test_csrf_is_still_required_and_does_not_consume_budget(self):
        self.assertEqual(self.client.post('/mcx/login/', {'username': 'invalid', 'password': 'bad'}).status_code, 403)
        for _ in range(3):
            self.assertEqual(self.attempt().status_code, 200)

    def test_cache_failure_fails_closed_without_authenticating(self):
        with patch('config.admin_site.cache.add', side_effect=ConnectionError('cache unavailable')):
            self.assertEqual(self.attempt().status_code, 503)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_real_admin_can_login_but_suspended_admin_cannot(self):
        admin = get_user_model().objects.create_user(username='admin-login', password='Valid-admin-password-2026!', is_staff=True, is_superuser=True)
        UserSuspension.objects.create(user=admin, reason='Restricted')
        form = {'username': admin.username, 'password': 'Valid-admin-password-2026!'}
        response = self.client.post('/mcx/login/', form, HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        admin.suspensions.update(ends_at=timezone.now()-timedelta(seconds=1))
        response = self.client.post('/mcx/login/', form, HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/mcx/')
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get('/mcx/').status_code, 200)
