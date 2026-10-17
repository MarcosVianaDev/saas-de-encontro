from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import connection, connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.events.models import Event, EventAdministrator
from apps.moderation.models import ModerationCase
from apps.notifications.models import Notification
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantPhoto, ParticipantProfile
from apps.reports.models import Report, ReportEvidence

from .social_safety import relevant_reporter_count, thresholds


class ReportFixtures:
    def setUp(self):
        super().setUp()
        self.owner = get_user_model().objects.create_user(
            username='report-manager', is_superuser=True,
        )
        self.organization = Organization.objects.create(name='Cliente de teste')
        self.event = self.new_event('Evento de teste')
        EventAdministrator.objects.create(event=self.event, user=self.owner, role='ADMIN')
        self.actor = self.participant('reporter')
        self.target = self.participant('reported')
        self.other = self.participant('other-reporter')
        self.url = f'/api/reports/{self.target.pk}/'
        self.payload = {
            'reasons': ['Outro'], 'description': 'Relato para revisão pela equipe.',
            'evidence': {'context': 'Contexto original'},
        }

    def new_event(self, name):
        return Event.objects.create(
            organization=self.organization, name=name, responsible=self.owner,
            mode='PHYSICAL', latitude='-23.550000', longitude='-46.630000',
            state='RUNNING', starts_at=timezone.now(), ends_at=timezone.now() + timedelta(hours=2),
        )

    def participant(self, name, event=None, user=None):
        user = user or get_user_model().objects.create_user(username=name)
        participant = EventParticipant.objects.create(
            user=user, event=event or self.event, is_active=True,
            registration_status='ACTIVE', activated_at=timezone.now(),
            last_seen_at=timezone.now(), location_consent=True,
        )
        ParticipantProfile.objects.create(
            participant=participant, first_name=name, last_name='Teste',
            birth_year=1990, birth_month=1, gender='Homens',
            bio='Um perfil de teste completo para verificar as regras de denúncia e moderação.',
        )
        return participant

    def client_for(self, participant):
        client = APIClient()
        client.force_login(participant.user)
        session = client.session
        session['event_id'] = str(participant.event_id)
        session['navigation'] = 'participant'
        session.save()
        client.defaults['HTTP_X_EVENT_ID'] = session.get('event_id', '')
        return client


class ReportAbuseTests(ReportFixtures, TestCase):
    def test_repeated_requests_create_only_one_report_and_do_not_deactivate_target(self):
        client = self.client_for(self.actor)
        response = client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        report = Report.objects.get(reporter=self.actor, reported=self.target)
        audit_count = AuditLog.objects.count()

        changed_payload = {
            'reasons': ['Fraude ou golpe'], 'description': 'Tentativa de alterar a denúncia.',
            'evidence': {'context': 'Outra evidência'},
        }
        for attempt in range(25):
            with self.subTest(attempt=attempt):
                response = client.post(self.url, changed_payload, format='json')
                if attempt < 9:
                    self.assertEqual(response.status_code, 400, response.content)
                    self.assertIn('já denunciou', str(response.json()))
                else:
                    self.assertEqual(response.status_code, 429, response.content)
                    self.assertGreater(int(response['Retry-After']), 0)

        report.refresh_from_db()
        self.assertEqual(report.description, self.payload['description'])
        self.assertEqual(report.reasons, self.payload['reasons'])
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(ModerationCase.objects.count(), 1)
        self.assertEqual(ReportEvidence.objects.count(), 1)
        self.assertEqual(report.evidence.get().description, 'Contexto original')
        self.assertEqual(AuditLog.objects.count(), audit_count)
        self.assertFalse(Notification.objects.exists())
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.assertEqual(self.target.deactivation_reason, '')

    def test_unfounded_report_cannot_be_submitted_again_by_same_reporter(self):
        Report.objects.create(
            reporter=self.actor, reported=self.target, reason='Revisada', is_unfounded=True,
        )
        response = self.client_for(self.actor).post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(relevant_reporter_count(self.target), 0)

    def test_uniqueness_is_scoped_to_participant_pair_and_event(self):
        client = self.client_for(self.actor)
        self.assertEqual(client.post(self.url, self.payload, format='json').status_code, 201)
        self.assertEqual(client.post(f'/api/reports/{self.other.pk}/', self.payload, format='json').status_code, 201)
        another_event = self.new_event('Outro evento')
        reporter = self.participant('same-reporter', event=another_event, user=self.actor.user)
        target = self.participant('same-target', event=another_event, user=self.target.user)
        response = self.client_for(reporter).post(f'/api/reports/{target.pk}/', self.payload, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Report.objects.count(), 3)

    def test_legacy_duplicates_do_not_inflate_thresholds_or_case_priority(self):
        Report.objects.bulk_create([
            Report(reporter=self.actor, reported=self.target, reason='Denúncia histórica')
            for _ in range(25)
        ])
        thresholds(self.target)
        self.assertEqual(relevant_reporter_count(self.target), 1)
        response = self.client_for(self.other).post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(relevant_reporter_count(self.target), 2)
        self.assertEqual(Report.objects.count(), 26)
        self.assertEqual(ModerationCase.objects.get(report__reporter=self.other).priority, 1)
        self.assertFalse(Notification.objects.exists())
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.assertEqual(self.target.deactivation_reason, '')

    def test_irrelevant_or_unattributed_reports_do_not_count(self):
        Report.objects.create(reporter=self.actor, reported=self.target, reason='Administrativa', is_administrative=True)
        Report.objects.create(reporter=self.other, reported=self.target, reason='Infundada', is_unfounded=True)
        Report.objects.bulk_create([
            Report(reported=self.target, reason='Sem denunciante') for _ in range(25)
        ])
        foreign = self.participant('foreign', event=self.new_event('Evento externo'))
        Report.objects.create(reporter=foreign, reported=self.target, reason='Registro fora do evento')
        self.assertEqual(relevant_reporter_count(self.target), 0)
        thresholds(self.target)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)
        self.assertFalse(Notification.objects.exists())

    def test_valid_legacy_report_counts_once_even_with_an_unfounded_duplicate(self):
        Report.objects.create(reporter=self.actor, reported=self.target, reason='Infundada', is_unfounded=True)
        Report.objects.create(reporter=self.actor, reported=self.target, reason='Relevante')
        self.assertEqual(relevant_reporter_count(self.target), 1)

    def test_invalid_evidence_rolls_back_and_does_not_block_valid_submission(self):
        foreign = self.participant('foreign', event=self.new_event('Outro evento'))
        photo = ParticipantPhoto.objects.create(participant=foreign, storage_key='tests/foreign.jpg')
        client = self.client_for(self.actor)
        response = client.post(self.url, {
            **self.payload, 'evidence': {'photo': str(photo.pk)},
        }, format='json')
        self.assertEqual(response.status_code, 404, response.content)
        self.assertFalse(Report.objects.exists())
        self.assertFalse(ModerationCase.objects.exists())
        self.assertFalse(ReportEvidence.objects.exists())
        response = client.post(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, 201, response.content)


@skipUnlessDBFeature('has_select_for_update')
class ConcurrentReportTests(ReportFixtures, TransactionTestCase):
    def _fixture_teardown(self):
        if connection.vendor != 'postgresql':
            return super()._fixture_teardown()
        # Only Django's disposable test database may reset immutable audit rows.
        # Both audit guards remain enabled while the requests are exercised.
        self.assertTrue(connection.settings_dict['NAME'].startswith('test_'))
        with connection.cursor() as cursor:
            cursor.execute('ALTER TABLE audit_auditlog DISABLE TRIGGER audit_no_truncate')
        try:
            super()._fixture_teardown()
        finally:
            with connection.cursor() as cursor:
                cursor.execute('ALTER TABLE audit_auditlog ENABLE TRIGGER audit_no_truncate')

    def submit_concurrently(self, participants):
        barrier = Barrier(len(participants))

        def submit(participant):
            try:
                client = self.client_for(participant)
                barrier.wait(timeout=10)
                response = client.post(self.url, self.payload, format='json')
                return response.status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(participants)) as pool:
            return sorted(pool.map(submit, participants))

    def test_concurrent_duplicate_submissions_create_only_one_case(self):
        self.assertEqual(self.submit_concurrently([self.actor, self.actor]), [201, 400])
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(ModerationCase.objects.count(), 1)
        self.assertEqual(ReportEvidence.objects.count(), 1)
        self.assertEqual(AuditLog.objects.filter(action='case.created').count(), 1)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_concurrent_distinct_reporters_reach_twenty_without_duplicate_notifications(self):
        for index in range(18):
            reporter = self.participant(f'historical-reporter-{index}')
            Report.objects.create(reporter=reporter, reported=self.target, reason='Relevante')
        self.assertEqual(self.submit_concurrently([self.actor, self.other]), [201, 201])
        self.assertEqual(relevant_reporter_count(self.target), 20)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)
        self.assertEqual(self.target.deactivation_reason, 'REPORT_REVIEW')
        self.assertFalse(hasattr(self.target, 'ban'))
        self.assertEqual(Notification.objects.filter(kind='reports10').count(), 1)
        self.assertEqual(Notification.objects.filter(kind='reports20').count(), 1)
        self.assertEqual(Notification.objects.filter(kind='profile_review').count(), 1)
