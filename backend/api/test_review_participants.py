from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.events.models import Event
from apps.interactions.models import Interaction, InteractionHistory
from apps.matches.models import Match
from apps.messaging.models import Conversation
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ParticipantPreference
from apps.reports.models import Block
from api.services import DEFAULT_FILTERS


class ReviewParticipantsTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(organization=Organization.objects.create(name='Cliente'),
                                         name='Evento', mode='ONLINE', state='RUNNING')
        self.actor = self.person('actor')
        ParticipantPreference.objects.create(participant=self.actor, filters=DEFAULT_FILTERS.copy())
        self.passed = self.person('passed')
        self.liked = self.person('liked')
        self.client = APIClient()
        self.client.force_login(self.actor.user)
        self.client.defaults['HTTP_X_EVENT_ID'] = str(self.event.pk)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session['navigation'] = 'participant'
        session.save()
        self.decide(self.passed, 'PASS')
        self.decide(self.liked, 'LIKE')

    def person(self, name, height=170, event=None):
        participant = EventParticipant.objects.create(event=event or self.event,
            user=get_user_model().objects.create_user(username=name), is_active=True)
        ParticipantProfile.objects.create(participant=participant, first_name=name,
                                         birth_month=1, birth_year=1995, height_cm=height)
        return participant

    def decide(self, person, decision):
        response = self.client.post(f'/api/interactions/{person.pk}/', {'decision': decision}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def review(self):
        response = self.client.post('/api/discovery/review/', {}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_only_pass_is_restored_and_history_survives_repeated_reviews_and_reload(self):
        data = self.review()
        self.assertEqual(data['count'], 1)
        self.assertEqual([person['id'] for person in data['data']['discovery']], [str(self.passed.pk)])
        self.assertNotIn(str(self.passed.pk), data['data']['seen'])
        self.assertIn(str(self.liked.pk), data['data']['seen'])
        interaction = Interaction.objects.get(participant=self.actor, target=self.passed)
        self.assertEqual(interaction.decision, 'PASS')
        self.assertEqual(interaction.history.count(), 1)
        self.assertEqual(self.review()['count'], 0)
        self.assertEqual([person['id'] for person in self.client.get('/api/discovery/').json()], [str(self.passed.pk)])
        self.decide(self.passed, 'PASS')
        self.assertEqual(self.client.get('/api/discovery/').json(), [])
        self.assertEqual(interaction.history.count(), 2)
        self.assertEqual(self.review()['count'], 1)

    def test_reevaluated_pass_can_be_liked_and_create_match(self):
        Interaction.objects.create(participant=self.passed, target=self.actor, decision='LIKE')
        self.review()
        response = self.decide(self.passed, 'LIKE')
        self.assertEqual(response['match']['id'], str(self.passed.pk))
        self.assertEqual(Match.objects.count(), 1)
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(self.review()['count'], 0)
        self.assertEqual(InteractionHistory.objects.filter(interaction__participant=self.actor,
            interaction__target=self.passed).count(), 2)

    def test_current_filters_and_visibility_and_event_scope_are_respected(self):
        blocked = self.person('blocked')
        self.decide(blocked, 'PASS')
        Block.objects.create(participant=blocked, target=self.actor)
        inactive = self.person('inactive')
        self.decide(inactive, 'PASS')
        EventParticipant.objects.filter(pk=inactive.pk).update(is_active=False)
        other = Event.objects.create(organization=self.event.organization, name='Outro', mode='ONLINE', state='RUNNING')
        foreign = self.person('foreign', event=other)
        Interaction.objects.create(participant=self.actor, target=foreign, decision='PASS')
        preference = self.actor.preference
        preference.filters = {**DEFAULT_FILTERS, 'minHeight': 180}
        preference.save()
        self.assertEqual(self.review()['count'], 0)
        preference.filters = DEFAULT_FILTERS.copy()
        preference.save()
        self.assertEqual([person['id'] for person in self.review()['data']['discovery']], [str(self.passed.pk)])
        self.assertFalse(Interaction.objects.filter(target__in=[blocked, inactive, foreign], review_pending=True).exists())

    def test_closed_event_cannot_review_passes(self):
        Event.objects.filter(pk=self.event.pk).update(state='CLOSED')
        self.assertEqual(self.client.post('/api/discovery/review/', {}, format='json').status_code, 403)
        self.assertFalse(Interaction.objects.filter(review_pending=True).exists())
