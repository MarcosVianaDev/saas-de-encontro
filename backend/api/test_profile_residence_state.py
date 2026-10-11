from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.events.models import Event
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ParticipantPhoto
from api.services import person_payload


class ProfileResidenceStateTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username='participant')
        event = Event.objects.create(organization=Organization.objects.create(name='Cliente'),
                                     name='Evento', mode='ONLINE', state='OPEN')
        self.participant = EventParticipant.objects.create(user=user, event=event)
        ParticipantProfile.objects.create(participant=self.participant)
        for index in range(3):
            ParticipantPhoto.objects.create(participant=self.participant, is_primary=index == 0,
                position=index, visibility='PRE_MATCH', storage_key=f'/images/{index}.jpg')
        self.client = APIClient()
        self.client.force_login(user)
        session = self.client.session
        session['event_id'] = str(event.pk)
        session['navigation'] = 'participant'
        session.save()
        self.data = {'first': 'Pessoa', 'last': 'Teste', 'month': 1, 'year': 1990,
                     'gender': 'Prefiro não informar',
                     'bio': 'Uma descrição de perfil com mais de cinquenta caracteres para completar o cadastro.'}

    def save(self, **extra):
        return self.client.put('/api/profile/', {**self.data, **extra}, format='json')

    def test_saves_state_and_federal_district_and_exposes_on_card(self):
        for state in ['SP', 'DF']:
            response = self.save(residenceState=state)
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(self.client.get('/api/profile/').json()['profile']['residenceState'], state)
            self.participant.profile.refresh_from_db()
            self.assertEqual(self.participant.profile.residence_state, state)
            self.assertEqual(person_payload(self.participant)['residenceState'], state)

    def test_optional_omission_preserves_value_and_blank_clears_it(self):
        self.assertEqual(self.save().status_code, 200)
        self.assertEqual(self.save(residenceState='AC').status_code, 200)
        self.assertEqual(self.save().json()['profile']['residenceState'], 'AC')
        response = self.save(residenceState='')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['profile']['residenceState'], '')

    def test_invalid_state_is_rejected_without_changing_profile(self):
        self.save(residenceState='SP')
        self.assertEqual(self.save(residenceState='XX').status_code, 400)
        self.assertEqual(self.client.get('/api/profile/').json()['profile']['residenceState'], 'SP')
