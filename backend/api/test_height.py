from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from api.services import DEFAULT_FILTERS, discovery, person_payload
from apps.events.models import Event
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ParticipantPhoto, ParticipantPreference


class HeightTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(organization=Organization.objects.create(name='Cliente'),
                                         name='Evento', mode='ONLINE', state='RUNNING')
        self.actor = self.participant('actor')
        ParticipantPreference.objects.create(participant=self.actor, filters=DEFAULT_FILTERS.copy())
        for index in range(3):
            ParticipantPhoto.objects.create(participant=self.actor, is_primary=index == 0,
                position=index, visibility='PRE_MATCH', storage_key=f'/images/{index}.jpg')
        self.client = APIClient()
        self.client.force_login(self.actor.user)
        self.client.defaults['HTTP_X_EVENT_ID'] = str(self.event.pk)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session['navigation'] = 'participant'
        session.save()
        self.profile = {'first': 'Pessoa', 'last': 'Teste', 'month': 1, 'year': 1995,
                        'gender': 'Prefiro não informar', 'bio': 'Uma descrição de perfil com mais de cinquenta caracteres para completar o cadastro.'}
        self.filters = {**DEFAULT_FILTERS, 'max': 100, 'purpose': ''}

    def participant(self, name, height=None, event=None):
        participant = EventParticipant.objects.create(event=event or self.event,
            user=get_user_model().objects.create_user(username=name), is_active=True)
        ParticipantProfile.objects.create(participant=participant, first_name=name, last_name='Teste',
                                         birth_month=1, birth_year=1995, height_cm=height)
        return participant

    def test_save_reload_omit_and_clear_height(self):
        response = self.client.put('/api/profile/', {**self.profile, 'height': 172}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.client.get('/api/profile/').json()['profile']['height'], 172)
        self.actor.profile.refresh_from_db()
        self.assertEqual(person_payload(self.actor)['height'], 172)
        self.assertEqual(self.client.put('/api/profile/', self.profile, format='json').json()['profile']['height'], 172)
        response = self.client.put('/api/profile/', {**self.profile, 'height': None}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()['profile']['height'])

    def test_invalid_height_is_rejected(self):
        for height in [0, 49, 251, 170.5, 'inválida']:
            with self.subTest(height=height):
                response = self.client.put('/api/profile/', {**self.profile, 'height': height}, format='json')
                self.assertEqual(response.status_code, 400)

    def test_filter_persists_and_applies_inclusive_bounds_and_optional_limits(self):
        short = self.participant('short', 159)
        lower = self.participant('lower', 160)
        upper = self.participant('upper', 180)
        tall = self.participant('tall', 181)
        missing = self.participant('missing')
        self.assertEqual(len(discovery(self.actor, self.filters)), 5)
        response = self.client.put('/api/filters/', {**self.filters, 'minHeight': 160, 'maxHeight': 180}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertCountEqual([p['id'] for p in response.json()['discovery']], [str(lower.pk), str(upper.pk)])
        bootstrap = self.client.get('/api/bootstrap/').json()
        self.assertEqual(bootstrap['filters']['minHeight'], 160)
        self.assertEqual(bootstrap['filters']['maxHeight'], 180)
        for bounds, expected in [({'minHeight': 180}, [upper, tall]), ({'maxHeight': 160}, [short, lower])]:
            self.assertCountEqual([p['id'] for p in discovery(self.actor, {**self.filters, **bounds})],
                                  [str(p.pk) for p in expected])
        response = self.client.put('/api/filters/', self.filters, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn(str(missing.pk), [p['id'] for p in response.json()['discovery']])

    def test_invalid_filter_bounds_are_rejected(self):
        for bounds in [{'minHeight': 181, 'maxHeight': 160}, {'minHeight': 49}, {'maxHeight': 251}]:
            with self.subTest(bounds=bounds):
                self.assertEqual(self.client.put('/api/filters/', {**self.filters, **bounds}, format='json').status_code, 400)
