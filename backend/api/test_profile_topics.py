import io

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.participants.models import EventParticipant
from apps.profiles.models import ProfileTopic
from demo.data import demo_id
from .serializers import ProfileSerializer


@override_settings(DEBUG=True, DEMO_USER_PASSWORD='Demo-password-2026!')
class ProfileTopicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', stdout=io.StringIO())

    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.get(email='admin-demo@eventconnect.local')
        self.actor = EventParticipant.objects.get(pk=demo_id('actor'))
        self.client.force_login(self.admin)

    def test_migration_seeds_topics_without_other(self):
        interests = ProfileTopic.objects.get(key='interests')
        purpose = ProfileTopic.objects.get(key='purpose')
        self.assertEqual(interests.name, 'Interesses')
        self.assertEqual(purpose.name, 'Finalidade no evento')
        self.assertEqual(len(interests.options), 7)
        self.assertEqual(len(purpose.options), 5)
        self.assertNotIn('Outros', interests.options + purpose.options)
        self.assertTrue(interests.multiple)
        self.assertFalse(purpose.multiple)

    def test_admin_creates_and_edits_topic_and_participant_cannot(self):
        body = {'action': 'save_topic', 'name': 'Idiomas', 'options': ['Português', 'Inglês', 'Inglês'], 'multiple': True}
        response = self.client.post('/api/global/', body, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        topic = ProfileTopic.objects.get(pk=response.json()['id'])
        self.assertEqual(topic.options, ['Português', 'Inglês'])
        response = self.client.post('/api/global/', {**body, 'id': str(topic.pk), 'multiple': False}, format='json')
        self.assertEqual(response.status_code, 200)
        topic.refresh_from_db()
        self.assertFalse(topic.multiple)
        self.assertIn(str(topic.pk), [t['id'] for t in self.client.get('/api/global/').json()['topics']])
        self.client.force_login(self.actor.user)
        self.assertEqual(self.client.post('/api/global/', body, format='json').status_code, 403)

    def test_dynamic_choices_and_single_or_multiple_validation(self):
        topic = ProfileTopic.objects.get(key='interests')
        topic.options = ['Leitura', 'Cinema']
        topic.save()
        serializer = ProfileSerializer()
        self.assertEqual(serializer.validate_interests(['Leitura']), ['Leitura'])
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            serializer.validate_interests(['Música'])
        topic.multiple = False
        topic.save()
        with self.assertRaises(ValidationError):
            serializer.validate_topicAnswers({'interests': ['Leitura', 'Cinema']})
        topic.multiple = True
        topic.save()
        self.assertEqual(serializer.validate_topicAnswers({'interests': ['Leitura', 'Cinema']}), {'interests': ['Leitura', 'Cinema']})

    def test_profile_saves_custom_and_builtin_topic_answers(self):
        topic = ProfileTopic.objects.create(key='languages', name='Idiomas', options=['Português', 'Inglês'], multiple=True)
        self.client.force_login(self.actor.user)
        session = self.client.session
        session['event_id'] = str(self.actor.event_id)
        session.save()
        data = self.client.get('/api/bootstrap/').json()
        self.assertIn(str(topic.pk), [t['id'] for t in data['profileTopics']])
        answers = {'languages': ['Português', 'Inglês'], 'interests': ['Arte'], 'purpose': ['Amizade']}
        response = self.client.put('/api/profile/', {**data['profile'], 'topicAnswers': answers}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        profile = response.json()['profile']
        self.assertEqual(profile['topicAnswers'], answers)
        self.assertEqual(profile['interests'], ['Arte'])
        self.assertEqual(profile['purpose'], 'Amizade')

    def test_empty_topic_options_are_rejected(self):
        response = self.client.post('/api/global/', {'action': 'save_topic', 'name': 'Empty', 'options': [], 'multiple': False}, format='json')
        self.assertEqual(response.status_code, 400)
