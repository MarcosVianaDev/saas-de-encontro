import copy
from datetime import timedelta
from unittest.mock import patch
from uuid import UUID

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import Event
from apps.matches.models import Match
from apps.messaging.models import Conversation, Message
from apps.moderation.models import UserSuspension
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ParticipantPhoto
from apps.reports.models import Block
from .services import current
from .sync import PAGE_SIZE, cursor_for


class ParticipantSyncTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.event = Event.objects.create(organization=Organization.objects.create(name='Sync client'),
                                         name='Sync event', mode='ONLINE', state='RUNNING')
        self.actor = self.participant('actor')
        self.peer = self.participant('peer')
        self.other = self.participant('other')
        self.conversation = self.conversation_for(self.actor, self.peer)
        self.other_conversation = self.conversation_for(self.actor, self.other)
        self.client = APIClient()
        self.client.force_login(self.actor.user)
        self.client.defaults['HTTP_X_EVENT_ID'] = str(self.event.pk)
        self.client.defaults['HTTP_X_APP_CONTEXT'] = 'participant'
        self.token = cursor_for(self.actor, self.now - timedelta(seconds=10))

    def participant(self, name, event=None):
        participant = EventParticipant.objects.create(
            user=get_user_model().objects.create_user(username=name), event=event or self.event,
            is_active=True, registration_status='ACTIVE', last_seen_at=self.now, presence='PRESENT',
        )
        ParticipantProfile.objects.create(participant=participant, first_name=name, last_name='Test',
                                         birth_year=1990, birth_month=1, gender='Homens')
        return participant

    def conversation_for(self, first, second):
        first, second = sorted([first, second], key=lambda participant: participant.pk.int)
        return Conversation.objects.create(match=Match.objects.create(participant=first, partner=second))

    def sync(self, token=None, **params):
        response = self.client.get('/api/sync/', {'cursor': token or self.token, **params})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_delta_contains_only_own_messages_status_and_match_peers(self):
        incoming = Message.objects.create(conversation=self.conversation, sender=self.peer, body='Incoming')
        outgoing = Message.objects.create(conversation=self.other_conversation, sender=self.actor, body='Outgoing')
        Message.objects.create(conversation=self.conversation_for(self.peer, self.other), sender=self.other, body='PRIVATE')
        with patch('api.services.bootstrap', side_effect=AssertionError('No bootstrap in sync')):
            data = self.sync()
        messages = {message['id']: message for message in data['messages']}
        self.assertEqual(set(messages), {str(incoming.pk), str(outgoing.pk)})
        self.assertEqual(messages[str(incoming.pk)]['peer'], str(self.peer.pk))
        self.assertTrue(messages[str(incoming.pk)]['unread'])
        self.assertTrue(messages[str(outgoing.pk)]['mine'])
        self.assertEqual(data['unread'], [str(self.peer.pk)])
        self.assertEqual(data['status']['event']['id'], str(self.event.pk))
        for key in ['profile', 'profileTopics', 'photos', 'people', 'chats', 'discovery', 'filters']:
            self.assertNotIn(key, data)

    def test_pagination_with_identical_timestamps_does_not_drop_messages(self):
        messages = [Message(conversation=self.conversation, sender=self.peer, body=f'Message {index}') for index in range(PAGE_SIZE * 2 + 3)]
        Message.objects.bulk_create(messages)
        timestamp = self.now - timedelta(seconds=1)
        Message.objects.filter(conversation=self.conversation).update(created_at=timestamp, updated_at=timestamp)
        token = self.token
        received = []
        for page in range(3):
            data = self.sync(token)
            self.assertLessEqual(len(data['messages']), PAGE_SIZE)
            received.extend(message['id'] for message in data['messages'])
            token = data['cursor']
            self.assertEqual(data['hasMore'], page < 2)
        self.assertEqual(len(received), len(set(received)))
        self.assertEqual(set(received), {str(message.pk) for message in messages})

    def test_empty_cursor_backfills_history_in_bounded_pages(self):
        old = Message.objects.create(conversation=self.conversation, sender=self.peer, body='Old message')
        Message.objects.filter(pk=old.pk).update(updated_at=self.now - timedelta(days=10))
        response = self.client.get('/api/sync/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual([message['id'] for message in response.json()['messages']], [str(old.pk)])

    def test_overlap_catches_late_visible_message_and_client_can_deduplicate(self):
        first = self.sync()
        message = Message.objects.create(conversation=self.conversation, sender=self.peer, body='Late commit')
        Message.objects.filter(pk=message.pk).update(updated_at=self.now - timedelta(seconds=30))
        data = self.sync(first['cursor'])
        self.assertEqual([row['id'] for row in data['messages']], [str(message.pk)])
        self.assertEqual([row['id'] for row in self.sync(data['cursor'])['messages']], [str(message.pk)])

    def test_cursor_is_signed_and_bound_to_participant_and_event(self):
        other_event = Event.objects.create(organization=self.event.organization, name='Other event', mode='ONLINE')
        other_participation = self.participant('foreign-actor', other_event)
        tokens = ['invalid', self.token + 'tampered', cursor_for(self.peer, self.now), cursor_for(other_participation, self.now)]
        for token in tokens:
            with self.subTest(token=token):
                self.assertEqual(self.client.get('/api/sync/', {'cursor': token}).status_code, 400)
        self.assertEqual(self.sync()['status']['event']['id'], str(self.event.pk))

    def test_foreign_event_data_and_read_markers_are_isolated(self):
        event = Event.objects.create(organization=self.event.organization, name='Foreign', mode='ONLINE')
        foreign = self.participant('foreign', event)
        peer = self.participant('foreign-peer', event)
        secret = Message.objects.create(conversation=self.conversation_for(foreign, peer), sender=peer, body='SECRET')
        self.assertNotIn(str(secret.pk), {row['id'] for row in self.sync()['messages']})
        response = self.client.post(f'/api/conversations/{foreign.pk}/read/', {'messages': [str(secret.pk)]}, format='json')
        self.assertEqual(response.status_code, 404)
        secret.refresh_from_db()
        self.assertIsNone(secret.read_at)

    def test_read_acknowledges_only_delivered_incoming_messages_from_selected_chat(self):
        incoming = Message.objects.create(conversation=self.conversation, sender=self.peer, body='Read this')
        outgoing = Message.objects.create(conversation=self.conversation, sender=self.actor, body='Mine')
        unrelated = Message.objects.create(conversation=self.other_conversation, sender=self.other, body='Other chat')
        undelivered = Message.objects.create(conversation=self.conversation, sender=self.peer, body='Not delivered')
        self.assertIsNone(Message.objects.get(pk=incoming.pk).read_at)
        self.sync()  # Polling by itself does not mark anything read.
        response = self.client.post(f'/api/conversations/{self.peer.pk}/read/', {
            'messages': [str(incoming.pk), str(outgoing.pk), str(unrelated.pk)],
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['read'], [str(incoming.pk)])
        self.assertIsNotNone(Message.objects.get(pk=incoming.pk).read_at)
        for message in [outgoing, unrelated, undelivered]:
            self.assertIsNone(Message.objects.get(pk=message.pk).read_at)
        row = next(row for row in self.sync()['messages'] if row['id'] == str(incoming.pk))
        self.assertFalse(row['unread'])

    def test_read_requests_are_bounded_and_repeated_ack_does_not_write(self):
        url = f'/api/conversations/{self.peer.pk}/read/'
        self.assertEqual(self.client.post(url, {'messages': [str(UUID(int=index)) for index in range(101)]}, format='json').status_code, 400)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.post(url, {'messages': []}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(any(query['sql'].lstrip().upper().startswith(('UPDATE ', 'INSERT ', 'DELETE ')) for query in queries))

    def test_match_end_block_and_event_status_are_visible_without_catalog(self):
        Block.objects.create(participant=self.peer, target=self.actor)
        self.other_conversation.match.is_active = False
        self.other_conversation.match.save()
        Event.objects.filter(pk=self.event.pk).update(state='PAUSED')
        data = self.sync()
        self.assertTrue(data['chatStates'][str(self.peer.pk)]['blocked'])
        self.assertFalse(data['chatStates'][str(self.other.pk)]['active'])
        peer = next(peer for peer in data['peers'] if peer['id'] == str(self.peer.pk))
        self.assertEqual(peer['name'], 'Usuário bloqueado')
        self.assertEqual(peer['bio'], '')
        self.assertEqual(data['status']['event']['state'], 'PAUSED')
        self.assertFalse(data['status']['socialAvailable'])

    def test_deactivation_and_account_sanctions_are_revalidated(self):
        EventParticipant.objects.filter(pk=self.actor.pk).update(is_active=False, registration_status='INACTIVE')
        data = self.sync()
        self.assertFalse(data['status']['active'])
        UserSuspension.objects.create(user=self.actor.user, reason='Review')
        self.assertEqual(self.client.get('/api/sync/').status_code, 403)

    def test_heartbeat_has_no_writes_inside_one_minute_and_updates_at_boundary(self):
        for seconds in [0, 5, 30, 59]:
            with patch('django.utils.timezone.now', return_value=self.now + timedelta(seconds=seconds)), CaptureQueriesContext(connection) as queries:
                self.sync()
            self.assertFalse(any(query['sql'].lstrip().upper().startswith('UPDATE ') for query in queries))
        with patch('django.utils.timezone.now', return_value=self.now + timedelta(seconds=60)), CaptureQueriesContext(connection) as queries:
            self.sync()
        self.assertEqual(sum(query['sql'].lstrip().upper().startswith('UPDATE ') for query in queries), 1)
        self.actor.refresh_from_db()
        self.assertEqual(self.actor.last_seen_at, self.now + timedelta(seconds=60))

    def test_stale_concurrent_snapshots_cannot_overwrite_a_fresh_heartbeat(self):
        EventParticipant.objects.filter(pk=self.actor.pk).update(last_seen_at=self.now - timedelta(minutes=2))
        self.actor.refresh_from_db()
        stale = [copy.copy(self.actor), copy.copy(self.actor)]
        request = RequestFactory().get('/api/sync/', HTTP_X_EVENT_ID=str(self.event.pk))
        request.user = self.actor.user
        request.session = {}
        with patch('api.services.get_object_or_404', side_effect=stale):
            with patch('django.utils.timezone.now', return_value=self.now):
                first = current(request)
            with patch('django.utils.timezone.now', return_value=self.now + timedelta(seconds=1)):
                second = current(request)
        self.assertEqual(first.last_seen_at, self.now)
        self.assertEqual(second.last_seen_at, self.now)
        self.assertEqual(EventParticipant.objects.get(pk=self.actor.pk).last_seen_at, self.now)

    def test_sync_cost_does_not_grow_with_event_population(self):
        # No match/profile changes in the delta window; a quiet poll must never
        # serialize participant cards or fetch the full catalog.
        old = self.now - timedelta(days=1)
        Match.objects.all().update(created_at=old, updated_at=old)
        EventParticipant.objects.all().update(updated_at=old)
        ParticipantProfile.objects.all().update(updated_at=old)
        with patch('api.sync.person_payload', side_effect=AssertionError('No unchanged profiles')):
            with CaptureQueriesContext(connection) as first_queries:
                first = self.sync()
            users = [get_user_model()(username=f'population-{index}') for index in range(500)]
            get_user_model().objects.bulk_create(users)
            EventParticipant.objects.bulk_create([EventParticipant(user=user, event=self.event, is_active=True) for user in users])
            with CaptureQueriesContext(connection) as second_queries:
                second = self.sync(first['cursor'])
        self.assertEqual(len(first_queries), len(second_queries))
        self.assertLessEqual(len(second_queries), 12)
        self.assertEqual(second['messages'], [])
        self.assertEqual(second['peers'], [])

    def test_catalog_reuses_prefetched_photos_without_per_profile_queries(self):
        for index in range(10):
            person = self.participant(f'catalog-{index}')
            ParticipantPhoto.objects.create(participant=person, storage_key=f'/images/catalog-{index}.jpg', is_primary=True)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/api/catalog/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()['people']), 12)
        self.assertLessEqual(len(queries), 12)
        self.assertIn('/images/catalog-0.jpg', [person['image'] for person in response.json()['people']])

    def test_event_closing_delivers_report_once_without_reloading_message_history(self):
        message = Message.objects.create(conversation=self.conversation, sender=self.peer, body='History retained')
        Event.objects.filter(pk=self.event.pk).update(state='CLOSED')
        data = self.sync(state='RUNNING')
        self.assertTrue(data['status']['event']['readOnly'])
        self.assertEqual(data['status']['discoveryReport']['matches'], 2)
        self.assertFalse(data['chatStates'][str(self.peer.pk)]['active'])
        self.assertIn(str(message.pk), {row['id'] for row in data['messages']})
        with patch('api.sync.discovery_report', side_effect=AssertionError('Report already received')):
            data = self.sync(data['cursor'], state='CLOSED')
        self.assertNotIn('discoveryReport', data['status'])

    def test_messages_created_between_pages_are_delivered_in_next_window(self):
        Message.objects.bulk_create([Message(conversation=self.conversation, sender=self.peer, body=str(index)) for index in range(101)])
        first = self.sync()
        self.assertTrue(first['hasMore'])
        late = Message.objects.create(conversation=self.conversation, sender=self.peer, body='Between pages')
        second = self.sync(first['cursor'])
        self.assertFalse(second['hasMore'])
        data = self.sync(second['cursor'])
        ids = {row['id'] for row in data['messages']}
        while data['hasMore']:
            data = self.sync(data['cursor'])
            ids.update(row['id'] for row in data['messages'])
        self.assertIn(str(late.pk), ids)
