from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as ModelValidationError
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.events.models import Event, EventAdministrator
from apps.notifications.models import Notification, SupportThread
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.constants import BIO_MIN_LENGTH, BIO_MAX_LENGTH
from apps.profiles.models import ParticipantPhoto, ParticipantProfile
from .profile_operations import validate_activation
from .serializers import ProfileSerializer


class BiographyValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='bio-participant')
        cls.manager = get_user_model().objects.create_user(username='bio-manager')
        cls.event = Event.objects.create(
            organization=Organization.objects.create(name='Biography validation'),
            name='Online event', mode='ONLINE', state='RUNNING', settings={'auto_activate_participants': True},
        )
        EventAdministrator.objects.create(event=cls.event, user=cls.manager, role='ADMIN')
        cls.participant = EventParticipant.objects.create(event=cls.event, user=cls.user)
        cls.profile = ParticipantProfile.objects.create(
            participant=cls.participant, first_name='Maria', last_name='Silva',
            birth_month=1, birth_year=1990, gender='Mulheres', bio='x' * BIO_MIN_LENGTH,
        )
        for index in range(3):
            ParticipantPhoto.objects.create(participant=cls.participant,
                storage_key=f'/images/bio-{index}.jpg', is_primary=index == 0, position=index)
        cls.source = SupportThread.objects.create(participant=cls.participant, subject='Correct biography')

    def test_serializer_accepts_boundaries_and_rejects_outside_them(self):
        payload = {'first': 'Maria', 'last': 'Silva', 'month': 1, 'year': 1990, 'gender': 'Mulheres'}
        for length, valid in [(49, False), (50, True), (200, True), (201, False)]:
            with self.subTest(length=length):
                serializer = ProfileSerializer(data={**payload, 'bio': 'x' * length})
                self.assertEqual(serializer.is_valid(), valid, serializer.errors)
                if not valid:
                    self.assertIn('bio', serializer.errors)

    def test_serializer_counts_trimmed_text(self):
        field = ProfileSerializer().fields['bio']
        self.assertEqual(field.run_validation(' ' + 'x' * BIO_MAX_LENGTH + ' '), 'x' * BIO_MAX_LENGTH)
        with self.assertRaises(ValidationError):
            field.run_validation(' ' * BIO_MIN_LENGTH)

    def test_model_validation_uses_the_same_limits_and_allows_incomplete_profile(self):
        for length, valid in [(0, True), (49, False), (50, True), (200, True), (201, False)]:
            with self.subTest(length=length):
                self.profile.bio = 'x' * length
                if valid:
                    self.profile.full_clean()
                else:
                    with self.assertRaises(ModelValidationError) as caught:
                        self.profile.full_clean()
                    self.assertIn('bio', caught.exception.message_dict)

    def test_activation_rejects_oversized_legacy_biography(self):
        for length, valid in [(49, False), (50, True), (200, True), (201, False)]:
            with self.subTest(length=length):
                self.participant.profile.bio = 'x' * length
                if valid:
                    validate_activation(self.participant)
                else:
                    with self.assertRaises(ValidationError):
                        validate_activation(self.participant)

    def test_admin_intervention_rejects_invalid_lengths_without_side_effects(self):
        client = APIClient()
        client.force_login(self.manager)
        url = f'/api/event-admin/participants/{self.participant.pk}/profile-intervention/'
        for length in [49, 201]:
            with self.subTest(length=length):
                response = client.post(url, {'action': 'edit_bio', 'bio': 'x' * length,
                    'reason': 'Correct biography', 'source': str(self.source.pk), 'kind': 'support'},
                    format='json', HTTP_X_EVENT_ID=str(self.event.pk))
                self.assertEqual(response.status_code, 400, response.content)
                self.assertIn('bio', response.json())
                self.profile.refresh_from_db()
                self.assertEqual(self.profile.bio, 'x' * BIO_MIN_LENGTH)
        self.assertFalse(AuditLog.objects.filter(action='profile.edit_bio').exists())
        self.assertFalse(Notification.objects.filter(participant=self.participant).exists())

    def test_admin_intervention_accepts_exact_boundaries(self):
        client = APIClient()
        client.force_login(self.manager)
        for length in [BIO_MIN_LENGTH, BIO_MAX_LENGTH]:
            response = client.post(f'/api/event-admin/participants/{self.participant.pk}/profile-intervention/',
                {'action': 'edit_bio', 'bio': 'x' * length, 'reason': 'Correct biography',
                 'source': str(self.source.pk), 'kind': 'support'}, format='json',
                HTTP_X_EVENT_ID=str(self.event.pk))
            self.assertEqual(response.status_code, 200, response.content)
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.bio, 'x' * length)
