from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import Event, EventAdministrator
from apps.organizations.models import Organization, OrganizationMember
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ParticipantPhoto, EventOutfitPhoto
from apps.passes.gifts import configure_initial_gift, grant_initial_gift, grant_due_initial_gifts
from apps.passes.models import ParticipantPass, PassActivation, EventPassOffer
from apps.notifications.models import Notification


class InitialGiftTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.admin = get_user_model().objects.create_user(username='admin', is_superuser=True)
        user = get_user_model().objects.create_user(username='participant')
        self.org = Organization.objects.create(name='Cliente')
        OrganizationMember.objects.create(organization=self.org, user=self.admin)
        self.event = Event.objects.create(organization=self.org, responsible=self.admin, name='Evento',
            mode='ONLINE', state='RUNNING', starts_at=self.now, ends_at=self.now + timedelta(hours=2))
        EventAdministrator.objects.create(event=self.event, user=self.admin)
        self.participant = EventParticipant.objects.create(event=self.event, user=user,
            is_active=True, activated_at=self.now, location_consent=True)
        ParticipantProfile.objects.create(participant=self.participant, first_name='Pessoa', last_name='Teste',
            birth_month=1, birth_year=1990, gender='Mulheres', bio='Uma descrição de perfil suficientemente longa para completar o cadastro.')
        for index in range(3):
            ParticipantPhoto.objects.create(participant=self.participant, storage_key=f'test-{index}.jpg', is_primary=index == 0)
        EventOutfitPhoto.objects.create(participant=self.participant, storage_key='outfit.jpg')
        self.config = {'enabled': True, 'name': 'Boas-vindas', 'delay_minutes': 0, 'duration_minutes': 0, 'reveal_limit': 3}

    def configure(self, **values):
        configure_initial_gift(self.event, {**self.config, **values}, self.admin)

    def test_immediate_gift_is_activated_notified_and_not_reissued(self):
        self.configure()
        for mode in ['ONLINE', 'PHYSICAL', 'HYBRID']:
            self.event.mode = mode
            self.event.save()
            self.assertEqual(grant_initial_gift(self.participant, self.now), mode == 'ONLINE')
        gift = self.participant.passes.get()
        self.assertEqual((gift.origin, gift.reveal_limit, gift.sale_amount), ('INITIAL_GIFT', 3, 0))
        self.assertTrue(PassActivation.objects.filter(participant_pass=gift).exists())
        self.assertEqual(Notification.objects.filter(participant=self.participant, kind='pass_activated').count(), 1)
        gift.revoked_at = self.now
        gift.save()
        self.assertFalse(grant_initial_gift(self.participant, self.now))

    def test_delayed_gift_is_not_early_and_late_activation_receives_it(self):
        self.configure(delay_minutes=10)
        self.assertEqual(grant_due_initial_gifts(self.now + timedelta(minutes=9)), 0)
        self.assertEqual(grant_due_initial_gifts(self.now + timedelta(minutes=10)), 1)
        self.assertEqual(grant_due_initial_gifts(self.now + timedelta(minutes=11)), 0)
        user = get_user_model().objects.create_user(username='late')
        late = EventParticipant.objects.create(event=self.event, user=user, is_active=True, activated_at=self.now + timedelta(minutes=15))
        self.assertTrue(grant_initial_gift(late, self.now + timedelta(minutes=15)))

    def test_no_gift_before_activation_or_after_event_end(self):
        self.configure()
        self.participant.is_active = False
        self.participant.save()
        self.assertFalse(grant_initial_gift(self.participant, self.now))
        self.participant.is_active = True
        self.participant.save()
        self.assertFalse(grant_initial_gift(self.participant, self.event.ends_at))
        self.event.state = 'CLOSED'
        Event.objects.filter(pk=self.event.pk).update(state='CLOSED')
        self.assertFalse(grant_initial_gift(self.participant, self.now))

    def test_duration_counts_from_grant_time(self):
        self.configure(duration_minutes=20, reveal_limit=0)
        self.assertTrue(grant_initial_gift(self.participant, self.now))
        self.assertEqual(self.participant.passes.get().expires_at, self.now + timedelta(minutes=20))

    def test_shortening_event_cannot_put_gift_after_event_end(self):
        self.configure(delay_minutes=10)
        self.event.ends_at = self.now + timedelta(minutes=5)
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.event.full_clean()

    def test_manual_activation_delivers_gift_for_every_modality(self):
        self.configure()
        client = APIClient()
        client.force_login(self.admin)
        session = client.session
        session['event_id'] = str(self.event.pk)
        session.save()
        client.defaults['HTTP_X_EVENT_ID'] = session.get('event_id', '')
        for mode in ['ONLINE', 'PHYSICAL', 'HYBRID']:
            self.event.mode = mode
            self.event.save()
            self.participant.is_active = False
            self.participant.activated_at = None
            self.participant.save()
            response = client.post(f'/api/event-admin/participants/{self.participant.pk}/activate/', {}, format='json')
            self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.participant.passes.count(), 1)

    def test_automatic_profile_activation_delivers_gift(self):
        self.configure()
        self.event.settings = {**self.event.settings, 'auto_activate_participants': True}
        self.event.save()
        self.participant.is_active = False
        self.participant.activated_at = None
        self.participant.save()
        client = APIClient()
        client.force_login(self.participant.user)
        session = client.session
        session['event_id'] = str(self.event.pk)
        session.save()
        client.defaults['HTTP_X_EVENT_ID'] = session.get('event_id', '')
        profile = client.get('/api/bootstrap/').json()['profile']
        response = client.put('/api/profile/', profile, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.participant.passes.count(), 1)

    def test_event_creation_validates_delay_before_end_and_rolls_back(self):
        self.admin.email = 'admin@example.com'
        self.admin.save()
        client = APIClient()
        client.force_login(self.admin)
        body = {'action': 'create_event', 'client': str(self.org.pk), 'responsible': self.admin.email,
            'event': 'Novo evento', 'mode': 'ONLINE', 'starts': self.now.isoformat(),
            'ends': (self.now + timedelta(minutes=30)).isoformat()}
        for values in [{'delay_minutes': 30}, {'delay_minutes': 31}, {'delay_minutes': -1}, {'reveal_limit': 0}]:
            response = client.post('/api/global/', {**body, 'initial_gift': {**self.config, **values}}, format='json')
            self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(Event.objects.count(), 1)
        self.assertFalse(EventPassOffer.objects.exists())
        response = client.post('/api/global/', {**body, 'initial_gift': {**self.config, 'delay_minutes': 29}}, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        event = Event.objects.get(pk=response.json()['id'])
        self.assertEqual(event.settings['initial_gift']['delay_minutes'], 29)
        self.assertEqual(event.pass_offers.get().price, 0)
