from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import Event, EventAdministrator
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantPhoto, ParticipantProfile


class AdminParticipantProfileTests(TestCase):
    def setUp(self):
        self.manager = get_user_model().objects.create_user(username='manager')
        self.guest = get_user_model().objects.create_user(username='guest')
        self.event = Event.objects.create(organization=Organization.objects.create(name='Cliente'), name='Evento', mode='ONLINE')
        self.membership = EventAdministrator.objects.create(event=self.event, user=self.manager, role='ADMIN')
        self.participant = EventParticipant.objects.create(event=self.event, user=self.guest)
        ParticipantProfile.objects.create(participant=self.participant, first_name='Maria', last_name='Silva',
            bio='Descrição do perfil', job='Designer', city='São Paulo', interests=['Música', 'Viagens'])
        self.primary = ParticipantPhoto.objects.create(participant=self.participant, storage_key='profiles/public.jpg', is_primary=True)
        self.extra = ParticipantPhoto.objects.create(participant=self.participant, storage_key='/images/extra.jpg', position=1)
        ParticipantPhoto.objects.create(participant=self.participant, storage_key='profiles/private.jpg', visibility='POST_MATCH', position=2)
        ParticipantPhoto.objects.create(participant=self.participant, storage_key='profiles/removed.jpg', removed_at=timezone.now())
        self.client = APIClient()
        self.login(self.manager)
        self.url = f'/api/event-admin/participants/{self.participant.pk}/profile/'

    def login(self, user):
        self.client.force_login(user)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session.save()

    def test_profile_has_public_photos_and_admin_content_urls(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        profile = response.json()
        self.assertEqual(profile['name'], 'Maria Silva')
        self.assertEqual(profile['bio'], 'Descrição do perfil')
        self.assertEqual(profile['job'], 'Designer')
        self.assertEqual(profile['interests'], ['Música', 'Viagens'])
        self.assertEqual(profile['image'], f'/api/event-admin/photos/{self.primary.pk}/content/')
        self.assertEqual(profile['photos'], [profile['image'], '/images/extra.jpg'])

    def test_all_roles_that_can_view_participants_can_open_profile(self):
        for role in ['ADMIN', 'MODERATOR', 'OPERATOR']:
            self.membership.role = role
            self.membership.save()
            self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_other_event_participants_cannot_be_viewed(self):
        other_event = Event.objects.create(organization=self.event.organization, name='Outro', mode='ONLINE')
        other = EventParticipant.objects.create(event=other_event, user=self.guest)
        self.assertEqual(self.client.get(f'/api/event-admin/participants/{other.pk}/profile/').status_code, 404)

    def test_non_members_and_inactive_members_cannot_view_profile(self):
        self.login(self.guest)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.login(self.manager)
        self.membership.is_active = False
        self.membership.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_missing_profile_and_primary_photo_use_fallback(self):
        self.participant.profile.delete()
        self.primary.removed_at = timezone.now()
        self.primary.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        profile = response.json()
        self.assertEqual(profile['image'], '/images/profile-placeholder.svg')
        self.assertEqual(profile['photos'], ['/images/extra.jpg'])
        self.assertEqual(profile['bio'], '')
