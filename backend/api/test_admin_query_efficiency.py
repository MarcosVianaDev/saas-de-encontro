from datetime import timedelta
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.events.models import Event, EventAdministrator
from apps.moderation.models import EventBan, EventSuspension, ModerationCase, ModerationNote, UserSuspension
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantPhoto, ParticipantProfile
from apps.reports.models import Block, Report, ReportEvidence
from .event_admin import admin_participants, participant_payload


class AdminQueryEfficiencyTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.owner = get_user_model().objects.create_user(username='owner', email='owner@example.invalid')
        self.event = Event.objects.create(organization=Organization.objects.create(name='Client'), name='Event', mode='ONLINE', state='RUNNING')
        self.membership = EventAdministrator.objects.create(user=self.owner, event=self.event, role='ADMIN')
        self.actor, self.target = self.populate(2)
        self.details([self.target])
        self.client = APIClient()
        self.client.force_login(self.owner)
        self.client.defaults.update(HTTP_X_EVENT_ID=str(self.event.pk), HTTP_X_APP_CONTEXT='administration')

    def populate(self, count):
        users = get_user_model().objects.bulk_create([
            get_user_model()(username=f'user-{uuid4()}', email=f'{uuid4()}@example.invalid') for _ in range(count)
        ])
        participants = EventParticipant.objects.bulk_create([
            EventParticipant(user=user, event=self.event, is_active=True, registration_status='ACTIVE', last_seen_at=self.now) for user in users
        ])
        ParticipantProfile.objects.bulk_create([
            ParticipantProfile(participant=p, first_name='Person', last_name=str(index), birth_year=1990, birth_month=1) for index, p in enumerate(participants)
        ])
        ParticipantPhoto.objects.bulk_create([
            ParticipantPhoto(participant=p, storage_key=f'private/{p.pk}.jpg', is_primary=True) for p in participants
        ])
        return participants

    def details(self, participants):
        reports = Report.objects.bulk_create([Report(reporter=self.actor, reported=p, reason='Relevant') for p in participants])
        cases = ModerationCase.objects.bulk_create([ModerationCase(report=report, assigned_to=self.owner) for report in reports])
        ModerationNote.objects.bulk_create([ModerationNote(case=case, author=self.owner, body='Internal note') for case in cases])
        ReportEvidence.objects.bulk_create([ReportEvidence(report=report, description='Evidence', snapshot={'visible': True}, storage_key=f'evidence/{report.pk}.bin') for report in reports])
        AuditLog.objects.bulk_create([AuditLog(actor=self.owner, action='case.created', object_label=ModerationCase._meta.label,
                                              object_id=case.pk, details={'event': str(self.event.pk)}) for case in cases])
        Block.objects.bulk_create([Block(participant=self.actor, target=p) for p in participants])

    def panel(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/api/event-admin/')
        self.assertEqual(response.status_code, 200, response.content)
        return response.json(), len(queries)

    def test_full_panel_query_count_is_constant_with_100_participants_cases_and_blocks(self):
        small, before = self.panel()
        self.details(self.populate(98))
        large, after = self.panel()
        self.assertEqual(len(small['participants']), 2)
        self.assertEqual(len(large['participants']), 100)
        self.assertEqual(len(large['cases']), 99)
        self.assertEqual(len(large['blockSignals']), 99)
        self.assertEqual(after, before, f'Queries grew from {before} to {after}')
        self.assertLessEqual(after, 25)
        self.assertEqual(large['metrics']['participants'], 100)
        self.assertEqual(large['metrics']['active'], 100)
        for case in large['cases']:
            self.assertEqual(case['notes'][0]['body'], 'Internal note')
            self.assertEqual(case['history'][0]['body'], 'Ocorrência criada')
            self.assertEqual(case['evidence'][0]['snapshot'], {'visible': True})
            self.assertTrue(case['evidence'][0]['content'].startswith(f'/api/events/{self.event.pk}/event-admin/evidence/'))

    def test_operator_query_count_is_constant_and_moderation_data_stays_hidden(self):
        EventAdministrator.objects.filter(pk=self.membership.pk).update(role='OPERATOR')
        _, before = self.panel()
        self.details(self.populate(98))
        data, after = self.panel()
        self.assertEqual(after, before)
        self.assertLessEqual(after, 20)
        self.assertEqual(len(data['participants']), 100)
        self.assertEqual(data['cases'], [])
        self.assertEqual(data['blockSignals'], [])
        for participant in data['participants']:
            self.assertIsNone(participant['reports'])
            self.assertIsNone(participant['blocks'])
            self.assertEqual(participant['reason'], '')

    def test_loaded_cards_do_not_query_and_counts_do_not_multiply_between_joins(self):
        third = self.populate(1)[0]
        Report.objects.bulk_create([
            Report(reporter=third, reported=self.target, reason='Second relevant'),
            Report(reporter=third, reported=self.target, reason='Unfounded', is_unfounded=True),
            Report(reported=self.target, reason='Administrative', is_administrative=True, created_by=self.owner),
        ])
        Block.objects.create(participant=third, target=self.target)
        # Hidden/removed primary photos must never replace the visible photo.
        ParticipantPhoto.objects.bulk_create([
            ParticipantPhoto(participant=self.target, storage_key='hidden.jpg', is_primary=True, visibility='POST_MATCH'),
            ParticipantPhoto(participant=self.target, storage_key='removed.jpg', is_primary=True, removed_at=self.now),
        ])
        participants = list(admin_participants(self.event, True, self.now))
        with self.assertNumQueries(0):
            cards = {p.pk: participant_payload(p, True) for p in participants}
        self.assertEqual(cards[self.target.pk]['reports'], 2)
        self.assertEqual(cards[self.target.pk]['blocks'], 2)
        self.assertIn('/event-admin/photos/', cards[self.target.pk]['image'])
        self.assertNotIn('hidden', cards[self.target.pk]['image'])

    def test_batched_sanctions_preserve_status_precedence_and_reasons(self):
        people = self.populate(7)
        global_suspended, global_expired, banned, revoked_ban, local_suspended, local_expired, inactive_user = people
        UserSuspension.objects.create(user=global_suspended.user, reason='Global', ends_at=self.now+timedelta(hours=1))
        UserSuspension.objects.create(user=global_expired.user, reason='Expired', ends_at=self.now-timedelta(seconds=1))
        EventBan.objects.create(participant=banned, reason='Ban')
        EventBan.objects.create(participant=revoked_ban, reason='Revoked', revoked_at=self.now)
        EventSuspension.objects.create(participant=local_suspended, actor=self.owner, reason='Local')
        EventSuspension.objects.create(participant=local_expired, actor=self.owner, reason='Expired', ends_at=self.now-timedelta(seconds=1))
        EventSuspension.objects.create(participant=local_expired, actor=self.owner, reason='Revoked', revoked_at=self.now)
        get_user_model().objects.filter(pk=inactive_user.user_id).update(is_active=False)
        cards = {p.pk: participant_payload(p, True) for p in admin_participants(self.event, True, self.now)}
        expected = ['Conta suspensa', 'Ativo', 'Banido', 'Ativo', 'Suspenso', 'Ativo', 'Conta suspensa']
        for person, status in zip(people, expected):
            raw = EventParticipant.objects.get(pk=person.pk)
            self.assertEqual(raw.operational_status, status)
            self.assertEqual(cards[person.pk]['status'], status)
        self.assertEqual(cards[banned.pk]['reason'], 'Ban')
        self.assertEqual(cards[local_suspended.pk]['reason'], 'Local')
        self.assertEqual(cards[local_expired.pk]['reason'], '')
        Event.objects.filter(pk=self.event.pk).update(state='CLOSED')
        closed = {p.pk: participant_payload(p, True)['status'] for p in admin_participants(self.event, True, self.now)}
        self.assertEqual(closed[banned.pk], 'Evento encerrado')
        self.assertEqual(closed[global_suspended.pk], 'Conta suspensa')
