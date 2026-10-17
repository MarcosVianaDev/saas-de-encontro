from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import Client, override_settings

from apps.events.models import Event, EventAdministrator
from apps.matches.models import Match
from apps.messaging.models import Conversation, Message
from apps.notifications.models import Notification
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant
from config.asgi import application
from config.testing import DisposableTransactionTestCase


@override_settings(DEBUG=True, ALLOWED_HOSTS=['testserver'], CSRF_TRUSTED_ORIGINS=[])
class RealtimeTests(DisposableTransactionTestCase):
    def setUp(self):
        self.event = Event.objects.create(organization=Organization.objects.create(name='Realtime'), name='Live', state='RUNNING')
        self.other_event = Event.objects.create(organization=self.event.organization, name='Other', state='RUNNING')
        self.actor = self.participant('actor')
        self.peer = self.participant('peer')
        self.stranger = self.participant('stranger')
        self.actor_elsewhere = EventParticipant.objects.create(user=self.actor.user, event=self.other_event)
        first, second = sorted([self.actor, self.peer], key=lambda participant: participant.pk.int)
        self.match = Match.objects.create(participant=first, partner=second)
        self.conversation = Conversation.objects.create(match=self.match)
        self.admin = get_user_model().objects.create_user(username='admin', is_superuser=True)
        self.operator = get_user_model().objects.create_user(username='operator')
        self.membership = EventAdministrator.objects.create(event=self.event, user=self.operator, role='OPERATOR')
        self.cookies = {}
        for user in [self.actor.user, self.peer.user, self.stranger.user, self.admin, self.operator]:
            client = Client()
            client.force_login(user)
            self.cookies[user.pk] = client.cookies[settings.SESSION_COOKIE_NAME].value
        self.sockets = []

    def participant(self, name):
        return EventParticipant.objects.create(user=get_user_model().objects.create_user(username=name), event=self.event, is_active=True)

    async def socket(self, user=None, event=None, context='participant', origin='http://testserver', host='testserver'):
        path = '/ws/global/' if context == 'global' else f'/ws/events/{(event or self.event).pk}/{context}/'
        headers = [(b'host', host.encode())]
        if origin is not None:
            headers.append((b'origin', origin.encode()))
        if user:
            headers.append((b'cookie', f'{settings.SESSION_COOKIE_NAME}={self.cookies[user.pk]}'.encode()))
        socket = WebsocketCommunicator(application, path, headers=headers)
        self.sockets.append(socket)
        accepted, code = await socket.connect()
        if accepted:
            self.assertEqual(await socket.receive_json_from(), {'type': 'ready'})
        return socket, accepted, code

    async def close_sockets(self):
        for socket in self.sockets:
            await socket.disconnect()

    @database_sync_to_async
    def commit(self, callback):
        with transaction.atomic():
            return callback()

    @async_to_sync
    async def test_rejects_anonymous_untrusted_origin_missing_origin_and_invalid_host(self):
        for kwargs in [{}, {'user': self.actor.user, 'origin': 'https://evil.invalid'},
                       {'user': self.actor.user, 'origin': None}, {'user': self.actor.user, 'host': 'evil.invalid'}]:
            _, accepted, _ = await self.socket(**kwargs)
            self.assertFalse(accepted)
        await self.close_sockets()

    @async_to_sync
    async def test_memberships_and_global_privileges_are_checked_against_url_not_session(self):
        for user, event, context, expected in [
            (self.actor.user, self.event, 'participant', True),
            (self.peer.user, self.other_event, 'participant', False),
            (self.operator, self.event, 'administration', True),
            (self.operator, self.other_event, 'administration', False),
            (self.actor.user, self.event, 'administration', False),
            (self.actor.user, None, 'global', False),
            (self.admin, None, 'global', True),
            (self.admin, self.other_event, 'administration', True),
        ]:
            _, accepted, _ = await self.socket(user, event, context)
            self.assertEqual(accepted, expected)
        await self.close_sockets()

    @async_to_sync
    async def test_message_invalidations_reach_only_both_parties_in_the_correct_event(self):
        actor, _, _ = await self.socket(self.actor.user)
        peer, _, _ = await self.socket(self.peer.user)
        stranger, _, _ = await self.socket(self.stranger.user)
        elsewhere, _, _ = await self.socket(self.actor.user, self.other_event)
        await self.commit(lambda: Message.objects.create(conversation=self.conversation, sender=self.peer, body='PRIVATE TEXT'))
        for socket in [actor, peer]:
            self.assertEqual(await socket.receive_json_from(), {'type': 'changed', 'topics': ['messages']})
        self.assertTrue(await stranger.receive_nothing(timeout=0.05))
        self.assertTrue(await elsewhere.receive_nothing(timeout=0.05))
        await self.close_sockets()

    @async_to_sync
    async def test_rollback_does_not_publish_and_committed_message_does(self):
        socket, _, _ = await self.socket(self.actor.user)

        def rollback():
            try:
                with transaction.atomic():
                    Message.objects.create(conversation=self.conversation, sender=self.peer, body='Rolled back')
                    raise ValueError('rollback')
            except ValueError:
                pass
        await self.commit(rollback)
        self.assertTrue(await socket.receive_nothing(timeout=0.05))
        await self.commit(lambda: Message.objects.create(conversation=self.conversation, sender=self.peer, body='Persisted'))
        self.assertEqual((await socket.receive_json_from())['topics'], ['messages'])
        await self.close_sockets()

    @async_to_sync
    async def test_bulk_notices_notify_their_recipient_and_not_other_participants(self):
        actor, _, _ = await self.socket(self.actor.user)
        peer, _, _ = await self.socket(self.peer.user)
        global_admin, _, _ = await self.socket(self.admin, context='global')
        event_admin, _, _ = await self.socket(self.admin, context='administration')
        elsewhere, _, _ = await self.socket(self.admin, self.other_event, context='administration')
        await self.commit(lambda: Notification.objects.bulk_create([
            Notification(participant=self.actor, event=self.event, title='Announcement'),
            Notification(recipient=self.admin, event=self.event, title='Admin alert'),
        ]))
        for socket in [actor, global_admin, event_admin]:
            self.assertEqual(await socket.receive_json_from(), {'type': 'changed', 'topics': ['notifications']})
        self.assertTrue(await peer.receive_nothing(timeout=0.05))
        self.assertTrue(await elsewhere.receive_nothing(timeout=0.05))
        await self.close_sockets()

    @async_to_sync
    async def test_event_status_fanout_stays_inside_its_event(self):
        actor, _, _ = await self.socket(self.actor.user)
        admin, _, _ = await self.socket(self.operator, context='administration')
        elsewhere, _, _ = await self.socket(self.actor.user, self.other_event)

        def pause():
            from apps.events.services import transition
            transition(self.event, 'PAUSED', actor=self.admin)
        await self.commit(pause)
        for socket in [actor, admin]:
            self.assertEqual((await socket.receive_json_from())['topics'], ['status'])
        self.assertTrue(await elsewhere.receive_nothing(timeout=0.05))
        await self.close_sockets()

    @async_to_sync
    async def test_sessions_and_revoked_membership_are_rechecked_on_long_connections(self):
        actor, _, _ = await self.socket(self.actor.user)
        admin, _, _ = await self.socket(self.operator, context='administration')

        @database_sync_to_async
        def revoke():
            from django.contrib.sessions.models import Session
            Session.objects.filter(session_key=self.cookies[self.actor.user.pk]).delete()
            EventAdministrator.objects.filter(pk=self.membership.pk).update(is_active=False)
        await revoke()
        for socket in [actor, admin]:
            await socket.send_json_to({'type': 'ping'})
            self.assertEqual(await socket.receive_output(), {'type': 'websocket.close', 'code': 4403})
        await self.close_sockets()

    @async_to_sync
    async def test_protocol_is_read_only_bounded_and_ping_is_limited(self):
        socket, _, _ = await self.socket(self.actor.user)
        await socket.send_json_to({'type': 'ping'})
        self.assertEqual(await socket.receive_json_from(), {'type': 'pong'})
        await socket.send_json_to({'type': 'ping'})
        self.assertEqual((await socket.receive_output())['code'], 4429)
        for payload in ['{', 'x' * 257, '{"type":"message","body":"spam"}']:
            socket, _, _ = await self.socket(self.actor.user)
            await socket.send_to(text_data=payload)
            self.assertEqual((await socket.receive_output())['code'], 4400)
        await self.close_sockets()

    @async_to_sync
    async def test_connections_are_rate_limited_per_account(self):
        with patch('realtime.consumers.time.time', return_value=100000):
            for index in range(21):
                _, accepted, code = await self.socket(self.actor.user)
                self.assertEqual(accepted, index < 20)
                if index == 20:
                    self.assertEqual(code, 4429)
        await self.close_sockets()

    def test_redis_failure_does_not_fail_a_committed_write(self):
        with patch('realtime.publishing.get_channel_layer') as layer, self.assertLogs('realtime.publishing', level='ERROR'):
            layer.return_value.group_send.side_effect = ConnectionError('Offline')
            with transaction.atomic():
                Notification.objects.create(participant=self.actor, title='Saved')
        self.assertTrue(Notification.objects.filter(title='Saved').exists())

    @async_to_sync
    async def test_production_rejects_http_origins_and_accepts_https(self):
        with override_settings(DEBUG=False):
            _, accepted, _ = await self.socket(self.actor.user)
            self.assertFalse(accepted)
            _, accepted, _ = await self.socket(self.actor.user, origin='https://testserver')
            self.assertTrue(accepted)
        await self.close_sockets()

    @async_to_sync
    async def test_inactive_user_is_rejected(self):
        await database_sync_to_async(get_user_model().objects.filter(pk=self.actor.user.pk).update)(is_active=False)
        _, accepted, _ = await self.socket(self.actor.user)
        self.assertFalse(accepted)
        await self.close_sockets()
