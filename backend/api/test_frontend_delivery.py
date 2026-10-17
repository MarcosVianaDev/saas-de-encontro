from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.events.models import Event, EventAdministrator
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant


class FrontendDeliveryTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.person = users.objects.create_user(username='spa-participant')
        self.manager = users.objects.create_user(username='spa-manager', is_staff=True)
        self.global_user = users.objects.create_user(username='spa-global', is_superuser=True)
        self.unrelated = users.objects.create_user(username='spa-unrelated')
        org = Organization.objects.create(name='SPA client')
        self.event = Event.objects.create(organization=org, name='SPA event', mode='ONLINE')
        EventParticipant.objects.create(user=self.person, event=self.event)
        self.membership = EventAdministrator.objects.create(user=self.manager, event=self.event)
        self.client = APIClient()

    def authorize(self, audience, **headers):
        return self.client.get('/api/frontend/authorize/', {'audience': audience}, **headers)

    def login(self, user, navigation, event=True):
        self.client.force_login(user)
        session = self.client.session
        session['navigation'] = navigation
        if event:
            session['event_id'] = str(self.event.pk)
        session.save()

    def test_anonymous_gets_no_authenticated_bundle(self):
        for audience in ['participant', 'event-manager', 'global']:
            self.assertEqual(self.authorize(audience).status_code, 401)
        self.assertEqual(self.client.get('/api/frontend/route/').json()['path'], '/')

    def test_participant_cannot_download_management_even_with_forged_headers(self):
        self.login(self.person, 'participant')
        self.assertEqual(self.authorize('participant').status_code, 204)
        for audience in ['event-manager', 'global']:
            response = self.authorize(audience, HTTP_X_APP_CONTEXT='global', HTTP_X_ROLE='ADMIN')
            self.assertEqual(response.status_code, 403)
            self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(self.client.get('/api/global/').status_code, 403)
        self.assertEqual(self.client.get('/api/event-admin/', HTTP_X_EVENT_ID=str(self.event.pk)).status_code, 404)

    def test_manager_gets_only_management_until_also_a_participant(self):
        self.login(self.manager, 'administration')
        self.assertEqual(self.authorize('event-manager').status_code, 204)
        self.assertEqual(self.authorize('global').status_code, 403)
        self.assertEqual(self.authorize('participant').status_code, 403)
        EventParticipant.objects.create(user=self.manager, event=self.event)
        self.assertEqual(self.authorize('participant').status_code, 204)

    def test_revoked_membership_takes_effect_without_new_login(self):
        self.login(self.manager, 'administration')
        self.membership.is_active = False
        self.membership.save()
        self.assertEqual(self.authorize('event-manager').status_code, 403)
        self.assertEqual(self.client.get('/api/frontend/route/').status_code, 403)

    def test_staff_flag_is_not_global_authorization(self):
        self.login(self.manager, 'administration')
        self.assertEqual(self.authorize('global').status_code, 403)
        self.login(self.unrelated, 'participant')
        for audience in ['participant', 'event-manager', 'global', '../global', 'unknown']:
            self.assertEqual(self.authorize(audience).status_code, 403)

    def test_global_gets_full_spa_even_in_event_context(self):
        for navigation in ['global', 'administration', 'participant']:
            self.login(self.global_user, navigation)
            response = self.client.get('/api/frontend/route/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['audience'], 'global')
            self.assertTrue(response.json()['path'].startswith('/spa/global/'))
        for audience in ['participant', 'event-manager', 'global']:
            self.assertEqual(self.authorize(audience).status_code, 204)

    def test_route_uses_verified_context_and_draft_destination(self):
        self.login(self.manager, 'administration')
        self.assertEqual(self.client.get('/api/frontend/route/').json()['path'], '/spa/event-manager/#admin-dashboard')
        self.assertEqual(self.client.get('/api/frontend/route/', HTTP_X_APP_CONTEXT='global').status_code, 403)
        self.login(self.person, 'participant')
        self.assertEqual(self.client.get('/api/frontend/route/').json()['path'], '/spa/participant/#perfil')
        self.login(self.global_user, 'administration')
        self.assertEqual(self.client.get('/api/frontend/route/').json()['path'], '/spa/global/#admin-event')

    def test_selection_stays_in_login_router(self):
        self.login(self.person, 'selection', event=False)
        self.assertEqual(self.client.get('/api/frontend/route/').json(), {'audience': 'login', 'path': '/'})
