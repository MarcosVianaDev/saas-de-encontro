from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from rest_framework.test import APIClient

from api.services import DEFAULT_FILTERS
from apps.events.models import Event
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantPhoto, ParticipantPreference, ParticipantProfile, ProfileTopic


class TopicFilterTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(username='topic-admin')
        self.event = Event.objects.create(organization=Organization.objects.create(name='Cliente'),
                                         name='Evento', mode='ONLINE', state='RUNNING')
        self.language = ProfileTopic.objects.create(key='languages', name='Idiomas',
            options=['Português', 'Inglês'], multiple=True, show_in_filter=True, filter_multiple=True)
        self.hidden = ProfileTopic.objects.create(key='hidden', name='Somente perfil', options=['Resposta'])
        self.actor = self.participant('actor')
        self.preference = ParticipantPreference.objects.create(participant=self.actor, filters=DEFAULT_FILTERS.copy())
        for index in range(3):
            ParticipantPhoto.objects.create(participant=self.actor, is_primary=index == 0,
                position=index, visibility='PRE_MATCH', storage_key=f'/images/{index}.jpg')
        self.alice = self.participant('alice', 'Heterossexual', 'Português', ['Arte'], 'Amizade')
        self.bob = self.participant('bob', 'Homossexual', 'Inglês', ['Música'], 'Networking')
        self.carla = self.participant('carla', 'Bissexual', 'Inglês', ['Arte'], 'Amizade')
        self.missing = self.participant('missing')
        self.client = APIClient()
        self.client.force_login(self.actor.user)
        self.client.defaults['HTTP_X_EVENT_ID'] = str(self.event.pk)
        self.filters = {**DEFAULT_FILTERS, 'max': 100}

    def participant(self, name, orientation=None, language=None, interests=None, purpose=''):
        participant = EventParticipant.objects.create(event=self.event,
            user=get_user_model().objects.create_user(username=name), is_active=True)
        answers = {'hidden': ['Resposta']}
        if orientation:
            answers['orientation'] = [orientation]
        if language:
            answers['languages'] = [language]
        ParticipantProfile.objects.create(participant=participant, first_name=name, last_name='Teste',
            birth_month=1, birth_year=1995, gender='Mulheres', interests=interests or [], purpose=purpose,
            topic_answers=answers, bio='Uma descrição de perfil com mais de cinquenta caracteres para completar o cadastro.')
        return participant

    def save_filters(self, topics, **extra):
        response = self.client.put('/api/filters/', {**self.filters, 'topics': topics, **extra}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def ids(self, data):
        return {person['id'] for person in data['discovery']}

    def test_orientation_seed_is_editable_single_choice_and_idempotent(self):
        topic = ProfileTopic.objects.get(key='orientation')
        self.assertEqual(topic.name, 'Orientação')
        self.assertEqual(topic.options, ['Heterossexual', 'Homossexual', 'Bissexual'])
        self.assertFalse(topic.multiple)
        self.assertFalse(topic.filter_multiple)
        self.assertTrue(topic.show_in_filter)
        self.assertTrue(ProfileTopic.objects.get(key='interests').show_in_filter)
        self.assertTrue(ProfileTopic.objects.get(key='purpose').show_in_filter)
        topic.options.append('Pansexual')
        topic.filter_multiple = True
        topic.show_in_filter = False
        topic.save()
        migration = import_module('apps.profiles.migrations.0010_profiletopic_filters_and_orientation')
        migration.seed_filter_topics(apps, SimpleNamespace(connection=connection))
        topic.refresh_from_db()
        self.assertIn('Pansexual', topic.options)
        self.assertTrue(topic.filter_multiple)
        self.assertFalse(topic.show_in_filter)
        self.assertEqual(ProfileTopic.objects.filter(key='orientation').count(), 1)

    def test_only_global_admin_can_create_edit_and_hide_a_filter_topic(self):
        body = {'action': 'save_topic', 'name': 'Atividades', 'options': ['Dança'],
                'multiple': True, 'showInFilter': True, 'filterMultiple': False}
        self.assertEqual(self.client.post('/api/global/', body, format='json').status_code, 403)
        self.client.force_login(self.admin)
        response = self.client.post('/api/global/', body, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        topic = ProfileTopic.objects.get(pk=response.json()['id'])
        self.assertTrue(topic.show_in_filter)
        self.assertFalse(topic.filter_multiple)
        # Clients that omit the new field must preserve an existing choice.
        response = self.client.post('/api/global/', {key: value for key, value in
            {**body, 'id': str(topic.pk)}.items() if key != 'showInFilter'}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        topic.refresh_from_db()
        self.assertTrue(topic.show_in_filter)
        response = self.client.post('/api/global/', {**body, 'id': str(topic.pk), 'showInFilter': False}, format='json')
        self.assertEqual(response.status_code, 200)
        topic.refresh_from_db()
        self.assertFalse(topic.show_in_filter)
        listed = next(item for item in self.client.get('/api/global/').json()['topics'] if item['id'] == str(topic.pk))
        self.assertFalse(listed['showInFilter'])

    def test_bootstrap_and_catalog_only_expose_filter_answers_for_enabled_visible_topics(self):
        for path in ['/api/bootstrap/', '/api/catalog/']:
            data = self.client.get(path).json()
            topics = {topic['key']: topic for topic in data['profileTopics']}
            self.assertTrue(topics['orientation']['showInFilter'])
            self.assertFalse(topics['hidden']['showInFilter'])
            alice = next(person for person in data['people'] if person['id'] == str(self.alice.pk))
            self.assertEqual(alice['topicAnswers']['orientation'], ['Heterossexual'])
            self.assertNotIn('hidden', alice['topicAnswers'])

    def test_filter_combines_topics_and_accepts_any_of_the_selected_options(self):
        ProfileTopic.objects.filter(key='orientation').update(filter_multiple=True)
        selected = {'orientation': ['Homossexual', 'Bissexual'], 'languages': ['Inglês']}
        data = self.save_filters(selected)
        self.assertEqual(self.ids(data), {str(self.bob.pk), str(self.carla.pk)})
        data = self.save_filters({**selected, 'purpose': ['Amizade']})
        self.assertEqual(self.ids(data), {str(self.carla.pk)})
        reloaded = self.client.get('/api/bootstrap/').json()
        self.assertEqual(reloaded['filters']['topics'], {**selected, 'purpose': ['Amizade']})
        self.assertEqual(self.ids(self.client.get('/api/catalog/').json()), {str(self.carla.pk)})
        self.assertEqual(len(self.save_filters({})['discovery']), 4)

    def test_single_filter_choice_is_independent_from_profile_choice_and_can_be_changed(self):
        # Languages accepts multiple profile answers, but its filter can be single.
        self.language.filter_multiple = False
        self.language.save()
        response = self.client.put('/api/filters/', {**self.filters,
            'topics': {'languages': ['Português', 'Inglês']}}, format='json')
        self.assertEqual(response.status_code, 400)
        self.client.force_login(self.admin)
        response = self.client.post('/api/global/', {'action': 'save_topic', 'id': str(self.language.pk),
            'name': self.language.name, 'options': self.language.options, 'multiple': True,
            'showInFilter': True, 'filterMultiple': True}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.client.force_login(self.actor.user)
        data = self.save_filters({'languages': ['Português', 'Inglês']})
        self.assertEqual(len(data['discovery']), 3)
        self.language.refresh_from_db()
        self.assertTrue(self.language.multiple)
        self.assertTrue(self.language.filter_multiple)
        self.language.filter_multiple = False
        self.language.save()
        data = self.client.get('/api/bootstrap/').json()
        self.assertEqual(data['filters']['topics']['languages'], ['Português'])
        self.assertEqual(self.ids(data), {str(self.alice.pk)})

    def test_hidden_topic_and_removed_options_stop_filtering_stored_preferences(self):
        self.save_filters({'languages': ['Inglês']})
        self.language.show_in_filter = False
        self.language.save()
        data = self.client.get('/api/bootstrap/').json()
        self.assertEqual(len(data['discovery']), 4)
        self.assertNotIn('languages', data['filters']['topics'])
        self.assertEqual(len(self.client.get('/api/catalog/').json()['discovery']), 4)
        self.language.show_in_filter = True
        self.language.options = ['Português']
        self.language.save()
        self.assertEqual(len(self.client.get('/api/bootstrap/').json()['discovery']), 4)

    def test_legacy_interests_are_filtered_but_hidden_interests_do_not_restrict_results(self):
        data = self.save_filters({}, interests=['Arte'])
        self.assertEqual(self.ids(data), {str(self.alice.pk), str(self.carla.pk)})
        ProfileTopic.objects.filter(key='interests').update(show_in_filter=False)
        data = self.client.get('/api/bootstrap/').json()
        self.assertEqual(len(data['discovery']), 4)
        self.assertEqual(data['filters']['interests'], [])

    def test_disabled_event_topics_cannot_be_used_even_if_globally_filterable(self):
        self.event.settings = {'participant_topics': [
            {'topic': str(self.language.pk), 'enabled': True, 'required': False, 'minimum': 1},
        ]}
        self.event.save()
        data = self.client.get('/api/bootstrap/').json()
        self.assertEqual([topic['key'] for topic in data['profileTopics']], ['languages'])
        response = self.client.put('/api/filters/', {**self.filters, 'topics': {'orientation': ['Bissexual']}}, format='json')
        self.assertEqual(response.status_code, 400)
        self.preference.filters = {**self.filters, 'topics': {'orientation': ['Bissexual']}}
        self.preference.save()
        self.assertEqual(len(self.client.get('/api/catalog/').json()['discovery']), 4)

    def test_invalid_filter_keys_options_and_shapes_are_rejected_and_duplicates_removed(self):
        for selected in [{'unknown': ['Option']}, {'hidden': ['Resposta']},
                         {'orientation': ['Inválida']}, {'orientation': 'Bissexual'}, []]:
            with self.subTest(selected=selected):
                response = self.client.put('/api/filters/', {**self.filters, 'topics': selected}, format='json')
                self.assertEqual(response.status_code, 400, response.content)
        data = self.save_filters({'orientation': ['Bissexual', 'Bissexual']})
        self.assertEqual(data['filters']['topics'], {'orientation': ['Bissexual']})

    def test_orientation_profile_save_single_choice_and_updated_catalog_validation(self):
        data = self.client.get('/api/bootstrap/').json()
        body = {**data['profile'], 'topicAnswers': {'orientation': ['Bissexual']}}
        response = self.client.put('/api/profile/', body, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['profile']['topicAnswers']['orientation'], ['Bissexual'])
        for selected in [['Inválida'], ['Heterossexual', 'Bissexual']]:
            response = self.client.put('/api/profile/', {**body, 'topicAnswers': {'orientation': selected}}, format='json')
            self.assertEqual(response.status_code, 400)
        topic = ProfileTopic.objects.get(key='orientation')
        topic.options.append('Pansexual')
        topic.save()
        response = self.client.put('/api/profile/', {**body, 'topicAnswers': {'orientation': ['Pansexual']}}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
