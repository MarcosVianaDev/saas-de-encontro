import io
from datetime import timedelta
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from apps.events.models import Event, EventAdministrator
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile
from apps.moderation.models import EventSuspension, EventBan, ModerationCase, ModerationAction
from apps.audit.models import AuditLog
from apps.reports.models import Report
from apps.reports.models import Block, ReportEvidence
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import tempfile
from demo.data import demo_id


@override_settings(DEBUG=True, DEMO_USER_PASSWORD='Demo-password-2026!')
class EventAdministrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', stdout=io.StringIO())
        cls.event = Event.objects.get(pk=demo_id('event.current'))
        cls.owner = get_user_model().objects.get(email='admin-demo@eventconnect.local')
        cls.owner.is_superuser = False
        cls.owner.save(update_fields=['is_superuser'])
        cls.actor = EventParticipant.objects.get(pk=demo_id('actor'))
        cls.peer = EventParticipant.objects.get(pk=demo_id('person.1'))
        cls.other_event = Event.objects.create(organization=cls.event.organization, name='Outro evento', state='OPEN', ends_at=timezone.now()+timedelta(days=1))

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(self.owner)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session.save()

    def role(self, value):
        EventAdministrator.objects.filter(user=self.owner, event=self.event).update(role=value)

    def login_as(self, user):
        self.client.force_login(user)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session.save()

    def token(self, event=None):
        return signing.dumps(str((event or self.event).pk), salt='event-join')

    def action(self, action, participant=None, reason='Motivo e contexto', **extra):
        p = participant or self.peer
        return self.client.post(f'/api/event-admin/participants/{p.pk}/action/', {'action': action, 'reason': reason, **extra}, format='json')

    def case(self):
        report = Report.objects.create(reporter=self.actor, reported=self.peer, reason='Relato para análise')
        return ModerationCase.objects.create(report=report)

    def case_action(self, case, action, **extra):
        return self.client.post(f'/api/event-admin/cases/{case.pk}/action/', {'action': action, 'reason': 'Justificativa', **extra}, format='json')

    def test_admin_login_without_participant_and_session_restore(self):
        self.assertFalse(self.owner.event_participations.exists())
        self.client.logout()
        response = self.client.post('/api/auth/login/', {'email': self.owner.email, 'password': 'Demo-password-2026!'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['navigation'], 'administration')
        self.assertTrue(self.client.get('/api/session/').json()['authenticated'])
        self.assertEqual(self.client.get('/api/bootstrap/').json()['navigation'], 'administration')

    def test_participant_login_and_no_admin_authority(self):
        self.client.logout()
        response = self.client.post('/api/auth/login/', {'email': self.actor.user.email, 'password': 'Demo-password-2026!'}, format='json')
        self.assertEqual(response.json()['data']['navigation'], 'selection')
        self.client.post('/api/contexts/',{'key':f'participant:{self.event.pk}'},format='json')
        self.assertEqual(self.client.get('/api/event-admin/').status_code, 404)
        self.assertEqual(self.action('suspend').status_code, 404)

    def test_admin_with_multiple_contexts_logs_in_directly(self):
        EventAdministrator.objects.create(user=self.owner, event=self.other_event)
        participant = EventParticipant.objects.create(user=self.owner, event=self.event)
        ParticipantProfile.objects.create(participant=participant, first_name='Owner', last_name='Test')
        self.client.logout()
        response = self.client.post('/api/auth/login/', {'email': self.owner.email, 'password': 'Demo-password-2026!'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['navigation'], 'administration')
        self.assertNotIn('contexts', response.json()['data'])
        self.assertEqual(self.client.get('/api/bootstrap/').json()['navigation'], 'administration')
        self.assertEqual(self.client.get('/api/contexts/').json()['navigation'], 'administration')
        self.assertEqual(self.client.get('/api/event-admin/').status_code, 200)

    def test_existing_admin_selection_session_restores_directly_to_panel(self):
        session = self.client.session
        session['navigation'] = 'selection'
        session.pop('event_id', None)
        session.save()
        response = self.client.get('/api/bootstrap/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['navigation'], 'administration')
        self.assertEqual(self.client.session['navigation'], 'administration')
        self.assertEqual(self.client.get('/api/event-admin/').status_code, 200)

    def test_admin_login_through_invite_still_opens_participant_access(self):
        self.client.logout()
        response = self.client.post('/api/auth/login/', {'email': self.owner.email,
            'password': 'Demo-password-2026!', 'invite': self.token(self.other_event)}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['navigation'], 'participant')
        self.assertEqual(response.json()['data']['event']['id'], str(self.other_event.pk))

    def test_admin_data_scoped_and_private_social_content_absent(self):
        response = self.client.get('/api/event-admin/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotIn(str(demo_id('history.target')), [p['id'] for p in data['participants']])
        for p in data['participants']:
            self.assertNotIn('chats', p)
            self.assertNotIn('matches', p)
            self.assertNotIn('filters', p)
        foreign = EventParticipant.objects.get(pk=demo_id('history.target'))
        self.assertEqual(self.action('ban', foreign, confirmed=True).status_code, 404)
        self.assertEqual(self.client.post('/api/event-admin/', {'event': str(self.other_event.pk)}).status_code, 404)

    def test_operator_cannot_moderate_or_view_sensitive_context(self):
        self.role('OPERATOR')
        self.case()
        data = self.client.get('/api/event-admin/').json()
        self.assertEqual(data['cases'], [])
        self.assertIsNone(data['participants'][0]['reports'])
        self.assertIsNone(data['metrics']['blocks'])
        self.assertEqual(self.action('suspend').status_code, 403)

    def test_moderator_cannot_ban_or_reopen(self):
        self.role('MODERATOR')
        self.assertEqual(self.action('ban', confirmed=True).status_code, 403)
        case = self.case()
        self.assertEqual(self.case_action(case, 'resolve').status_code, 200)
        self.assertEqual(self.case_action(case, 'reopen').status_code, 403)

    def test_event_suspension_is_scoped_reversible_and_enforced(self):
        self.assertEqual(self.action('suspend').status_code, 200)
        self.assertTrue(EventSuspension.objects.filter(participant=self.peer).exists())
        self.login_as(self.actor.user)
        ids = [p['id'] for p in self.client.get('/api/bootstrap/').json()['people']]
        self.assertNotIn(str(self.peer.pk), ids)
        self.login_as(self.peer.user)
        self.assertEqual(self.client.get('/api/bootstrap/').status_code, 403)
        other = EventParticipant.objects.create(event=self.other_event, user=self.peer.user)
        ParticipantProfile.objects.create(participant=other)
        session = self.client.session
        session['event_id'] = str(self.other_event.pk)
        session.save()
        self.assertEqual(self.client.get('/api/bootstrap/').status_code, 200)
        self.client.force_login(self.owner)
        session = self.client.session
        session['event_id'] = str(self.event.pk)
        session.save()
        self.assertEqual(self.action('reactivate').status_code, 200)
        self.assertIsNotNone(EventSuspension.objects.get(participant=self.peer).revoked_at)

    def test_ban_requires_confirmation_and_reason_and_is_enforced(self):
        self.assertEqual(self.action('ban').status_code, 400)
        self.assertEqual(self.action('ban', reason='', confirmed=True).status_code, 400)
        self.assertEqual(self.action('ban', confirmed=True).status_code, 200)
        self.assertTrue(EventBan.objects.filter(participant=self.peer).exists())
        self.login_as(self.peer.user)
        self.assertEqual(self.client.get('/api/bootstrap/').status_code, 403)
        self.assertTrue(AuditLog.objects.filter(action='participant.ban', object_id=self.peer.pk).exists())

    def test_case_assume_notes_sanction_resolution_and_reopening_preserve_history(self):
        case = self.case()
        for action in ['assume', 'note', 'suspend', 'resolve', 'reopen']:
            self.assertEqual(self.case_action(case, action).status_code, 200, action)
        case.refresh_from_db()
        self.assertIsNone(case.closed_at)
        self.assertEqual(case.assigned_to, self.owner)
        self.assertEqual(case.case_notes.count(), 1)
        self.assertEqual(ModerationAction.objects.filter(case=case).count(), 5)
        self.assertEqual(AuditLog.objects.filter(object_id=case.pk).count(), 5)

    def test_case_outside_event_is_not_accessible(self):
        case = ModerationCase.objects.get(pk=demo_id('case'))
        self.assertEqual(self.case_action(case, 'assume').status_code, 404)

    @override_settings(DEBUG=False)
    def test_invite_register_outside_debug_and_correct_event_link(self):
        self.client.logout()
        response = self.client.post('/api/auth/register/', {'email': 'qr-new@example.com', 'password': 'Good-password-2026!', 'invite': self.token(self.other_event), 'is_staff': True, 'is_superuser': True}, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()['data']['event']['id'], str(self.other_event.pk))
        user = get_user_model().objects.get(email='qr-new@example.com')
        self.assertFalse(user.event_administrations.exists())
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(self.client.session['event_id'], str(self.other_event.pk))
        self.assertEqual(self.client.session['navigation'], 'participant')
        self.assertEqual(user.event_participations.count(), 1)
        self.assertFalse(user.event_participations.get().is_active)

    def test_existing_user_invite_login_and_idempotent_join(self):
        self.client.logout()
        response = self.client.post('/api/auth/login/', {'email': self.actor.user.email, 'password': 'Demo-password-2026!', 'invite': self.token(self.other_event)}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['event']['id'], str(self.other_event.pk))
        for _ in range(2):
            self.assertEqual(self.client.post(f'/api/join/{self.token(self.other_event)}/', {}, format='json').status_code, 200)
        self.assertEqual(EventParticipant.objects.filter(user=self.actor.user, event=self.other_event).count(), 1)

    def test_qr_url_identifies_event_with_only_signed_invite(self):
        event = self.client.get('/api/event-admin/').json()['event']
        params = parse_qs(urlsplit(event['joinPath']).query)
        self.assertEqual(set(params), {'invite'})
        self.assertEqual(signing.loads(params['invite'][0], salt='event-join'), str(self.event.pk))
        response = self.client.get(f"/api/join/{params['invite'][0]}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], str(self.event.pk))

    def test_uuid_mismatch_rejected_for_preview_register_login_and_join(self):
        self.client.logout()
        counts = (get_user_model().objects.count(), EventParticipant.objects.count())
        body = {'email': 'mismatch@example.com', 'password': 'Good-password-2026!',
                'event': str(self.event.pk), 'invite': self.token(self.other_event)}
        self.assertEqual(self.client.get(f"/api/join/{body['invite']}/", {'event': body['event']}).status_code, 400)
        self.assertEqual(self.client.post('/api/auth/register/', body, format='json').status_code, 400)
        body.update(email=self.actor.user.email, password='Demo-password-2026!')
        self.assertEqual(self.client.post('/api/auth/login/', body, format='json').status_code, 400)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.client.force_login(self.actor.user)
        self.assertEqual(self.client.post(f"/api/join/{body['invite']}/", {'event': body['event']}, format='json').status_code, 400)
        self.assertEqual(counts, (get_user_model().objects.count(), EventParticipant.objects.count()))

    def test_malformed_uuid_and_missing_event_rejected_without_creating_accounts(self):
        self.client.logout()
        before = get_user_model().objects.count()
        for event_id in ['', 'invalid-uuid', str(uuid4())]:
            body = {'email': 'bad-uuid@example.com', 'password': 'Good-password-2026!',
                    'event': event_id, 'invite': self.token(self.other_event)}
            self.assertEqual(self.client.post('/api/auth/register/', body, format='json').status_code, 400)
        missing_id = str(uuid4())
        body = {'email': 'missing-event@example.com', 'password': 'Good-password-2026!',
                'event': missing_id, 'invite': signing.dumps(missing_id, salt='event-join')}
        self.assertEqual(self.client.post('/api/auth/register/', body, format='json').status_code, 404)
        self.assertEqual(get_user_model().objects.count(), before)

    def test_uuid_alone_does_not_allow_registration(self):
        self.client.logout()
        self.assertEqual(self.client.post('/api/auth/register/', {
            'email': 'uuid-only@example.com', 'password': 'Good-password-2026!',
            'event': str(self.other_event.pk),
        }, format='json').status_code, 403)
        self.assertFalse(get_user_model().objects.filter(email='uuid-only@example.com').exists())

    def test_closed_or_paused_event_cannot_register_new_accounts(self):
        self.client.logout()
        before = get_user_model().objects.count()
        for state in ['CLOSED', 'PAUSED']:
            event = Event.objects.create(organization=self.event.organization, name=f'Evento {state}', state=state, ends_at=timezone.now()+timedelta(days=1))
            self.assertEqual(self.client.post('/api/auth/register/', {
                'email': 'closed-event@example.com', 'password': 'Good-password-2026!',
                'event': str(event.pk), 'invite': self.token(event),
            }, format='json').status_code, 403)
        self.assertEqual(get_user_model().objects.count(), before)

    def test_invalid_expired_and_closed_event_invites_rejected(self):
        self.assertEqual(self.client.get('/api/join/not-a-token/').status_code, 400)
        with patch('django.core.signing.time.time', return_value=1):
            expired = self.token()
        self.assertEqual(self.client.get(f'/api/join/{expired}/').status_code, 400)
        self.event.ends_at = timezone.now() - timedelta(seconds=1)
        self.event.save()
        self.assertEqual(self.client.get(f'/api/join/{self.token()}/').status_code, 403)
        self.assertIsNone(self.client.get('/api/event-admin/').json()['event']['joinPath'])

    def test_join_requires_authentication_and_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.post(f'/api/join/{self.token()}/').status_code, 403)
        client.force_login(self.actor.user)
        self.assertEqual(client.post(f'/api/join/{self.token()}/').status_code, 403)
        token = client.get('/api/session/').json()['csrfToken']
        self.assertEqual(client.post(f'/api/join/{self.token()}/', HTTP_X_CSRFTOKEN=token).status_code, 200)

    def test_block_indicators_do_not_create_cases_or_sanctions(self):
        Block.objects.create(participant=self.actor, target=self.peer)
        data = self.client.get('/api/event-admin/').json()
        self.assertEqual(len(data['blockSignals']), 1)
        self.assertEqual(len(data['blockSignals'][0]['timeline']), 1)
        self.assertEqual(data['cases'], [])
        self.assertFalse(EventSuspension.objects.filter(participant=self.peer).exists())
        self.role('OPERATOR')
        self.assertEqual(self.client.get('/api/event-admin/').json()['blockSignals'], [])

    def test_evidence_download_requires_scope_role_and_is_audited(self):
        case = self.case()
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            key = default_storage.save('evidence/sample.txt', ContentFile(b'private evidence'))
            evidence = ReportEvidence.objects.create(report=case.report, storage_key=key)
            url = f'/api/event-admin/evidence/{evidence.pk}/content/'
            self.role('OPERATOR')
            self.assertEqual(self.client.get(url).status_code, 403)
            self.role('MODERATOR')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'private evidence')
            self.assertIn('no-store', response['Cache-Control'])
            self.assertTrue(AuditLog.objects.filter(action='evidence.viewed', object_id=evidence.pk).exists())
            foreign = ReportEvidence.objects.get(pk=demo_id('evidence'))
            self.assertEqual(self.client.get(f'/api/event-admin/evidence/{foreign.pk}/content/').status_code, 404)

    def test_resolved_cases_require_reopening_and_assignment_cannot_be_stolen(self):
        case = self.case()
        self.assertEqual(self.case_action(case, 'assume').status_code, 200)
        another = get_user_model().objects.create_user(username='other-moderator', password='Test-password-2026!')
        EventAdministrator.objects.create(user=another, event=self.event, role='MODERATOR')
        self.login_as(another)
        self.assertEqual(self.case_action(case, 'assume').status_code, 400)
        self.login_as(self.owner)
        self.assertEqual(self.case_action(case, 'resolve').status_code, 200)
        before = case.actions.count()
        self.assertEqual(self.case_action(case, 'note').status_code, 400)
        self.assertEqual(case.actions.count(), before)

    def test_administrative_report_notifies_without_creating_staff_participation(self):
        from apps.notifications.models import Notification
        response = self.action('report', category='Atendimento administrativo')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.owner.event_participations.exists())
        case = ModerationCase.objects.get(report__is_administrative=True)
        self.assertEqual(case.report.created_by, self.owner)
        self.assertIsNone(case.report.reporter)
        self.assertTrue(Notification.objects.filter(recipient=self.owner, event=self.event).exists())
        data = self.client.get('/api/event-admin/').json()
        self.assertEqual(data['cases'][0]['kind'], 'Administrativa')
        self.assertEqual(self.case_action(case, 'assume').status_code, 200)

    def test_recent_activity_is_real_and_separate_from_activation(self):
        self.assertEqual(self.client.get('/api/event-admin/').json()['metrics']['active'], 0)
        self.login_as(self.actor.user)
        self.assertEqual(self.client.get('/api/bootstrap/').status_code, 200)
        self.actor.refresh_from_db()
        self.assertIsNotNone(self.actor.last_seen_at)
        self.login_as(self.owner)
        data = self.client.get('/api/event-admin/').json()
        self.assertEqual(data['metrics']['active'], 1)
        EventParticipant.objects.filter(pk=self.actor.pk).update(last_seen_at=timezone.now()-timedelta(minutes=6))
        self.assertEqual(self.client.get('/api/event-admin/').json()['metrics']['active'], 0)
