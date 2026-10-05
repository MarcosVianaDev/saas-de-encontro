from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.events.models import Event, EventAdministrator
from apps.organizations.models import Organization, OrganizationMember


class GlobalClientTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.global_user = User.objects.create_user(
            username='global', email='global@example.com', is_superuser=True,
        )
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', is_staff=True,
        )
        self.client = APIClient()
        self.client.force_login(self.global_user)

    def new_client(self, **extra):
        return self.client.post('/api/global/', {
            'action': 'create_client', 'contact': 'Marcos Silva',
            'email': 'marcos@example.com', 'phone': '+55 11 98765-4321', **extra,
        }, format='json')

    def event_body(self, client):
        start = timezone.now() + timedelta(days=2)
        return {
            'action': 'create_event', 'client': str(client.pk),
            'event': 'Evento do cliente', 'starts': start.isoformat(),
            'ends': (start + timedelta(hours=3)).isoformat(),
            'responsible': self.owner.email,
        }

    def test_three_contact_fields_create_client_and_access_account_without_event(self):
        users = get_user_model().objects.count()
        response = self.new_client()
        self.assertEqual(response.status_code, 201, response.content)
        org = Organization.objects.get(pk=response.json()['id'])
        self.assertEqual((org.name, org.contact_name, org.contact_email, org.contact_phone), (
            'Marcos Silva', 'Marcos Silva', 'marcos@example.com', '+55 11 98765-4321',
        ))
        self.assertTrue(org.is_active)
        self.assertEqual(org.onboarding_draft['contact'], 'Marcos Silva')
        self.assertFalse(Event.objects.exists())
        self.assertFalse(EventAdministrator.objects.exists())
        self.assertEqual(get_user_model().objects.count(), users + 1)
        user = get_user_model().objects.get(email=org.contact_email)
        self.assertEqual(user.username, org.contact_email)
        self.assertEqual((user.first_name, user.last_name), ('Marcos', 'Silva'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_usable_password())
        self.assertTrue(OrganizationMember.objects.filter(organization=org, user=user).exists())
        self.assertEqual(response.json()['accessUser']['id'], str(user.pk))
        self.assertTrue(AuditLog.objects.filter(action='client.created', object_id=org.pk).exists())
        data = self.client.get('/api/global/').json()['clients'][0]
        self.assertEqual(data['phone'], org.contact_phone)
        self.assertEqual(data['accessUser'], response.json()['accessUser'])

    def test_account_names_use_first_and_last_words(self):
        for index, (name, first, last) in enumerate([
            ('Marcos Antônio Silva', 'Marcos', 'Silva'),
            ('  Ana   Maria  Souza  ', 'Ana', 'Souza'),
            ('Maria', 'Maria', 'Maria'),
        ]):
            response = self.new_client(contact=name, email=f'Person{index}@Example.com')
            self.assertEqual(response.status_code, 201, response.content)
            user = get_user_model().objects.get(email=f'person{index}@example.com')
            self.assertEqual((user.first_name, user.last_name), (first, last))

    def test_existing_email_or_username_rejects_client_without_overwriting_account(self):
        User = get_user_model()
        user = User.objects.create_user(username='Reserved@example.com', email='other@example.com', first_name='Original')
        count = User.objects.count()
        for email in ['OWNER@EXAMPLE.COM', 'reserved@example.com']:
            response = self.new_client(email=email)
            self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(Organization.objects.exists())
        self.assertEqual(User.objects.count(), count)
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Original')

    def test_account_and_client_creation_roll_back_together(self):
        User = get_user_model()
        count = User.objects.count()
        with patch('api.global_admin.OrganizationMember.objects.create', side_effect=RuntimeError('failure')):
            self.assertEqual(self.new_client().status_code, 500)
        self.assertEqual(User.objects.count(), count)
        self.assertFalse(Organization.objects.exists())
        self.assertFalse(AuditLog.objects.filter(action='account.created').exists())

    def test_created_account_can_log_in_as_event_administrator_after_password_setup(self):
        org = Organization.objects.get(pk=self.new_client().json()['id'])
        user = get_user_model().objects.get(email=org.contact_email)
        user.set_password('Client-test-password-123!')
        user.save()
        body = {**self.event_body(org), 'responsible': user.email}
        self.assertEqual(self.client.post('/api/global/', body, format='json').status_code, 201)
        visitor = APIClient()
        response = visitor.post('/api/auth/login/', {
            'email': user.email, 'password': 'Client-test-password-123!',
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['data']['navigation'], 'administration')

    def test_account_field_limits_reject_creation_without_partial_data(self):
        count = get_user_model().objects.count()
        for extra in [{'contact': 'A' * 151}, {'email': 'a' * 64 + '@' + 'b' * 63 + '.' + 'c' * 30 + '.com'}]:
            self.assertEqual(self.new_client(**extra).status_code, 400)
        self.assertEqual(get_user_model().objects.count(), count)
        self.assertFalse(Organization.objects.exists())

    def test_client_details_and_organization_can_be_completed_without_creating_event(self):
        org_id = self.new_client().json()['id']
        response = self.client.post('/api/global/', {
            'action': 'update_client', 'id': org_id, 'contact': 'Marcos atualizado',
            'email': 'updated@example.com', 'phone': '+55 11 99999-9999',
            'contact_role': 'Diretor', 'notes': 'Contato principal',
            'organization': 'ACME Eventos', 'description': 'Organização de eventos',
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        org = Organization.objects.get(pk=org_id)
        self.assertEqual(org.name, 'ACME Eventos')
        self.assertEqual(org.description, 'Organização de eventos')
        self.assertEqual(org.contact_name, 'Marcos atualizado')
        self.assertEqual(org.onboarding_draft['contact_role'], 'Diretor')
        self.assertEqual(org.onboarding_draft['notes'], 'Contato principal')
        self.assertEqual(Organization.objects.count(), 1)
        self.assertFalse(Event.objects.exists())
        self.assertTrue(AuditLog.objects.filter(action='client.updated', object_id=org.pk).exists())

    def test_client_validation_rejects_missing_or_invalid_contact_data(self):
        for extra in [{'contact': ''}, {'email': 'invalid'}, {'phone': ''}, {'phone': '1' * 51}]:
            self.assertEqual(self.new_client(**extra).status_code, 400)
        self.assertFalse(Organization.objects.exists())
        self.assertFalse(Event.objects.exists())

    def test_new_event_uses_existing_client_and_responsible_without_new_client(self):
        org = Organization.objects.get(pk=self.new_client().json()['id'])
        users = get_user_model().objects.count()
        response = self.client.post('/api/global/', self.event_body(org), format='json')
        self.assertEqual(response.status_code, 201, response.content)
        event = Event.objects.get(pk=response.json()['id'])
        self.assertEqual(event.organization, org)
        self.assertEqual(event.responsible, self.owner)
        self.assertEqual(event.state, 'SCHEDULED')
        self.assertTrue(EventAdministrator.objects.filter(event=event, user=self.owner, role='ADMIN').exists())
        self.assertEqual(Organization.objects.count(), 1)
        self.assertEqual(get_user_model().objects.count(), users)
        self.assertEqual(self.client.get('/api/global/').json()['events'][0]['organizationId'], str(org.pk))

    def test_same_client_can_have_multiple_independently_created_events(self):
        org = Organization.objects.get(pk=self.new_client().json()['id'])
        for name in ['Primeiro evento', 'Segundo evento']:
            body = {**self.event_body(org), 'event': name}
            self.assertEqual(self.client.post('/api/global/', body, format='json').status_code, 201)
        self.assertEqual(org.events.count(), 2)
        self.assertEqual(Organization.objects.count(), 1)

    def test_invalid_event_dates_or_unknown_responsible_roll_back_creation(self):
        org = Organization.objects.get(pk=self.new_client().json()['id'])
        users = get_user_model().objects.count()
        body = self.event_body(org)
        for extra in [{'ends': body['starts']}, {'starts': 'invalid'}, {'responsible': 'missing@example.com'}]:
            self.assertEqual(self.client.post('/api/global/', {**body, **extra}, format='json').status_code, 400)
        self.assertFalse(Event.objects.exists())
        self.assertFalse(EventAdministrator.objects.exists())
        self.assertEqual(get_user_model().objects.count(), users)

    def test_actions_are_restricted_to_global_administration(self):
        org = Organization.objects.create(name='Cliente')
        self.client.force_login(self.owner)
        self.assertEqual(self.new_client().status_code, 403)
        self.assertEqual(self.client.post('/api/global/', {
            'action': 'update_client', 'id': str(org.pk), 'contact': 'Alterado',
            'email': 'updated@example.com', 'phone': '11999999999',
        }, format='json').status_code, 403)
        self.assertEqual(self.client.post('/api/global/', self.event_body(org), format='json').status_code, 403)
        org.refresh_from_db()
        self.assertEqual(org.name, 'Cliente')
        self.assertFalse(Event.objects.exists())
