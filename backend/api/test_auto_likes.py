from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.organizations.models import Organization
from apps.events.models import Event, EventAdministrator
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile
from apps.interactions.models import Interaction
from apps.passes.models import EventPassOffer, PassType, ParticipantPass
from apps.passes.services import reveal_available, revealed_ids


class AutomaticLikesTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            organization=Organization.objects.create(name='Client'), name='Event',
            mode='ONLINE', state='RUNNING', ends_at=timezone.now() + timedelta(days=1),
        )
        self.people = []
        for index in range(4):
            user = get_user_model().objects.create_user(username=f'user{index}')
            p = EventParticipant.objects.create(event=self.event, user=user, is_active=True)
            ParticipantProfile.objects.create(participant=p, first_name=f'Person{index}', last_name='Test')
            self.people.append(p)
        self.target = self.people[0]
        for peer in self.people[1:]:
            Interaction.objects.create(participant=peer, target=self.target, decision='LIKE')
        self.offer = EventPassOffer.objects.create(
            event=self.event, price=0, pass_type=PassType.objects.create(name='Two likes', reveal_limit=2),
        )

    def test_grant_immediately_reveals_oldest_likes_within_limit(self):
        operator = get_user_model().objects.create_user(username='operator')
        EventAdministrator.objects.create(event=self.event, user=operator, role='OPERATOR', permissions=['passes'])
        client = APIClient()
        client.force_login(operator)
        session = client.session
        session['event_id'] = str(self.event.pk)
        session.save()
        response = client.post('/api/event-admin/passes/', {
            'action': 'grant', 'participant': str(self.target.pk), 'offer': str(self.offer.pk), 'origin': 'Test',
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(revealed_ids(self.target), {str(p.pk) for p in self.people[1:3]})
        participant_pass = self.target.passes.get()
        self.assertEqual(participant_pass.usages.count(), 2)
        self.assertEqual(reveal_available(self.target), 0)
        client.force_login(self.target.user)
        session = client.session
        session['event_id'] = str(self.event.pk)
        session.save()
        response = client.get('/api/likes-received/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['hidden'], 1)
        self.assertEqual(len(response.json()['people']), 2)

    def test_time_pass_reveals_all_and_expiry_hides_identities(self):
        participant_pass = ParticipantPass.objects.create(
            participant=self.target, offer=self.offer, expires_at=timezone.now() + timedelta(minutes=30),
        )
        self.assertEqual(reveal_available(self.target), 3)
        self.assertEqual(reveal_available(self.target), 0)
        self.assertEqual(participant_pass.usages.count(), 3)
        participant_pass.expires_at = timezone.now() - timedelta(seconds=1)
        participant_pass.save()
        self.assertEqual(revealed_ids(self.target), set())

    def test_new_like_is_revealed_automatically_with_valid_pass(self):
        from api.services import record_decision
        Interaction.objects.filter(target=self.target).delete()
        participant_pass = ParticipantPass.objects.create(participant=self.target, offer=self.offer, reveal_limit=2)
        record_decision(self.people[1], self.target, 'LIKE')
        self.assertEqual(participant_pass.usages.count(), 1)
        record_decision(self.people[1], self.target, 'LIKE')
        self.assertEqual(participant_pass.usages.count(), 1)

    def test_revoked_pass_does_not_reveal_hidden_likes(self):
        ParticipantPass.objects.create(
            participant=self.target, offer=self.offer, reveal_limit=2, revoked_at=timezone.now(),
        )
        self.assertEqual(reveal_available(self.target), 0)
