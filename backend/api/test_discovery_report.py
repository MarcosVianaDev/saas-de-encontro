from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.events.models import Event
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile
from apps.interactions.models import Interaction
from apps.matches.models import Match
from apps.messaging.models import Conversation, Message


class DiscoveryReportTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Report client')
        self.event = Event.objects.create(organization=self.organization, name='Report event', mode='ONLINE', state='CLOSED')
        self.actor = self.person('actor', self.event)
        self.first = self.person('first', self.event)
        self.second = self.person('second', self.event)
        self.third = self.person('third', self.event)
        self.client = APIClient()
        self.client.force_login(self.actor.user)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session['navigation'] = 'participant'
        session.save()

    def person(self, name, event, user=None):
        user = user or get_user_model().objects.create_user(username=name)
        participant = EventParticipant.objects.create(user=user, event=event, is_active=True)
        ParticipantProfile.objects.create(participant=participant, first_name=name, last_name='Test')
        return participant

    def conversation(self, actor, peer, active=True):
        first, second = sorted([actor, peer], key=lambda p: p.pk.int)
        return Conversation.objects.create(match=Match.objects.create(participant=first, partner=second, is_active=active))

    def test_report_counts_unique_people_in_current_event_including_ended_matches(self):
        for peer in [self.first, self.second]:
            Interaction.objects.create(participant=self.actor, target=peer, decision='LIKE')
        Interaction.objects.create(participant=self.actor, target=self.third, decision='PASS')
        for peer in [self.first, self.second, self.third]:
            Interaction.objects.create(participant=peer, target=self.actor, decision='LIKE')
        conversation = self.conversation(self.actor, self.first, active=False)
        Message.objects.create(conversation=conversation, sender=self.actor, body='Hello')
        Message.objects.create(conversation=conversation, sender=self.actor, body='Again')
        Message.objects.create(conversation=conversation, sender=self.first, body='Reply')
        received_only = self.conversation(self.actor, self.second)
        Message.objects.create(conversation=received_only, sender=self.second, body='Hello')
        self.conversation(self.actor, self.third)
        other_event = Event.objects.create(organization=self.organization, name='Other', mode='ONLINE', state='CLOSED')
        other_actor = self.person('actor elsewhere', other_event, self.actor.user)
        other_peer = self.person('other peer', other_event)
        Interaction.objects.create(participant=other_actor, target=other_peer, decision='LIKE')
        other_conversation = self.conversation(other_actor, other_peer)
        Message.objects.create(conversation=other_conversation, sender=other_actor, body='Other event')
        for state in ['CLOSED', 'ARCHIVED']:
            Event.objects.filter(pk=self.event.pk).update(state=state)
            response = self.client.get('/api/bootstrap/')
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(response.json()['discoveryReport'], {
                'likesSent': 2, 'likesReceived': 3, 'matches': 3, 'conversations': 1,
            })
            self.assertFalse(response.json()['socialAvailable'])
            self.assertEqual(response.json()['discovery'], [])

    def test_empty_report_contains_zero_counts(self):
        response = self.client.get('/api/bootstrap/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['discoveryReport'], {
            'likesSent': 0, 'likesReceived': 0, 'matches': 0, 'conversations': 0,
        })

    def test_report_is_unavailable_before_event_ends(self):
        for state in ['SCHEDULED', 'OPEN', 'RUNNING', 'PAUSED']:
            Event.objects.filter(pk=self.event.pk).update(state=state)
            response = self.client.get('/api/bootstrap/')
            self.assertEqual(response.status_code, 200)
            self.assertIsNone(response.json()['discoveryReport'])
