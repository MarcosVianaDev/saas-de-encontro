import json
import time
from importlib import import_module
from types import SimpleNamespace

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from apps.events.models import Event, EventAdministrator
from apps.moderation.models import EventBan, EventSuspension, UserSuspension
from apps.participants.models import EventParticipant
from .publishing import account_group, event_group

ACCESS_RECHECK_SECONDS = 30


class RealtimeConsumer(AsyncJsonWebsocketConsumer):
    """Authenticated, scoped, read-only invalidations; never accept chat writes."""

    @database_sync_to_async
    def authorized(self):
        # Reload the session as well as the user: another tab can log out, reset
        # the password or revoke access during a long-running connection.
        session = import_module(settings.SESSION_ENGINE).SessionStore(self.scope['session'].session_key)
        user = get_user(SimpleNamespace(session=session))
        if not user.is_authenticated or not user.is_active or user.pk != self.scope['user'].pk:
            return False
        if UserSuspension.objects.filter(user=user).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now())).exists():
            return False
        if self.context == 'global':
            return user.is_superuser
        if self.context == 'administration':
            return (Event.objects.filter(pk=self.event_id).exists() if user.is_superuser else
                    EventAdministrator.objects.filter(event_id=self.event_id, user=user, is_active=True).exists())
        participant = EventParticipant.objects.filter(user=user, event_id=self.event_id).first()
        return bool(participant and
                    not EventBan.objects.filter(participant=participant, revoked_at__isnull=True).exists() and
                    not EventSuspension.objects.filter(participant=participant, revoked_at__isnull=True).filter(
                        Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now())).exists())

    @database_sync_to_async
    def connection_allowed(self):
        key = f'realtime-connect:{self.scope["user"].pk}:{int(time.time() // 60)}'
        if cache.add(key, 1, timeout=65):
            return True
        return cache.incr(key) <= 20

    async def connect(self):
        self.groups_joined = []
        self.context = self.scope['url_route']['kwargs']['context']
        self.event_id = self.scope['url_route']['kwargs'].get('event_id')
        self.last_ping = 0
        if not self.scope['user'].is_authenticated:
            await self.close(code=4401)
            return
        if not await self.authorized():
            await self.close(code=4403)
            return
        if not await self.connection_allowed():
            await self.close(code=4429)
            return
        groups = [account_group(self.context, self.scope['user'].pk, self.event_id)]
        if self.event_id:
            groups.append(event_group(self.event_id))
        try:
            for group in groups:
                await self.channel_layer.group_add(group, self.channel_name)
                self.groups_joined.append(group)
        except Exception:
            await self.close(code=1013)
            return
        self.validated_at = time.monotonic()
        await self.accept()
        await self.send_json({'type': 'ready'})

    async def disconnect(self, code):
        for group in self.groups_joined:
            try:
                await self.channel_layer.group_discard(group, self.channel_name)
            except Exception:
                pass

    async def validate_access(self, force=False):
        if not force and time.monotonic() - self.validated_at < ACCESS_RECHECK_SECONDS:
            return True
        if not await self.authorized():
            await self.close(code=4403)
            return False
        self.validated_at = time.monotonic()
        return True

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        if bytes_data is not None or text_data is None or len(text_data) > 256:
            await self.close(code=4400)
            return
        try:
            payload = json.loads(text_data)
        except (ValueError, RecursionError):
            await self.close(code=4400)
            return
        if payload != {'type': 'ping'}:
            await self.close(code=4400)
            return
        now = time.monotonic()
        if now - self.last_ping < 10:
            await self.close(code=4429)
            return
        self.last_ping = now
        if await self.validate_access(force=True):
            await self.send_json({'type': 'pong'})

    async def realtime_changed(self, event):
        if await self.validate_access():
            await self.send_json({'type': 'changed', 'topics': event['topics']})
