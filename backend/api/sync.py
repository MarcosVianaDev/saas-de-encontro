from datetime import datetime, timedelta, timezone as dt_timezone
from uuid import UUID

from django.core import signing
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matches.models import Match
from apps.messaging.models import Message
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ParticipantPreference
from apps.reports.models import Block
from .services import (
    DEFAULT_FILTERS, current, discovery, discovery_report, match_for, participant_status,
    person_payload, visible_participants,
)

PAGE_SIZE = 100
OVERLAP = timedelta(minutes=2)
CURSOR_SALT = 'participant-sync-v1'


def cursor_for(participant, at, **page):
    return signing.dumps({
        'participant': str(participant.pk), 'event': str(participant.event_id),
        'at': at.isoformat(), **page,
    }, salt=CURSOR_SALT, compress=True)


def read_cursor(participant, token, now):
    if not token:
        return datetime.min.replace(tzinfo=dt_timezone.utc), now, None
    try:
        data = signing.loads(token, salt=CURSOR_SALT)
        if data['participant'] != str(participant.pk) or data['event'] != str(participant.event_id):
            raise ValueError
        at = datetime.fromisoformat(data['at'])
        if timezone.is_naive(at) or at > now:
            raise ValueError
        floor = datetime.fromisoformat(data['floor']) if 'floor' in data else at - OVERLAP
        if timezone.is_naive(floor) or floor > at:
            raise ValueError
        after = data.get('after')
        if after:
            after = (datetime.fromisoformat(after[0]), UUID(after[1]))
            if timezone.is_naive(after[0]) or not floor <= after[0] <= at:
                raise ValueError
        return floor, at if after else now, after
    except (signing.BadSignature, KeyError, ValueError, TypeError, OverflowError, IndexError):
        raise ValidationError('Cursor de sincronização inválido para este participante e evento.')


def message_payload(message, participant):
    return {
        'id': str(message['id']), 'text': message['body'],
        'mine': message['sender_id'] == participant.pk,
        'unread': message['sender_id'] != participant.pk and message['read_at'] is None,
        'time': timezone.localtime(message['created_at']).strftime('%H:%M'),
        'created': message['created_at'], 'updated': message['updated_at'],
    }


def mark_read(participant, match, identifiers=None, now=None):
    query = Message.objects.filter(conversation__match=match, read_at__isnull=True).exclude(sender=participant)
    if identifiers is not None:
        query = query.filter(pk__in=identifiers)
    identifiers = list(query.values_list('pk', flat=True))
    if identifiers:
        now = now or timezone.now()
        Message.objects.filter(pk__in=identifiers, read_at__isnull=True).update(read_at=now, updated_at=now)
        from realtime.publishing import participants_changed
        participants_changed([match.participant_id, match.partner_id], ['messages'])
    return [str(identifier) for identifier in identifiers]


class MessageReadView(APIView):
    def post(self, request, peer_id):
        participant = current(request)
        match = match_for(participant, peer_id)
        identifiers = serializers.ListField(child=serializers.UUIDField(), max_length=100).run_validation(request.data.get('messages'))
        now = timezone.now()
        return Response({'read': mark_read(participant, match, identifiers, now), 'updated': now})


class ParticipantSyncView(APIView):
    def get(self, request):
        participant = current(request)
        now = timezone.now()
        floor, until, after = read_cursor(participant, request.query_params.get('cursor'), now)
        matches = list(Match.objects.filter(
            Q(participant=participant) | Q(partner=participant),
            participant__event=participant.event, partner__event=participant.event,
        ).select_related(
            'conversation', 'participant__event', 'partner__event',
            'participant__user', 'partner__user', 'participant__ban', 'partner__ban',
        ))
        blocks = Block.objects.filter(Q(participant=participant) | Q(target=participant)).values_list('participant_id', 'target_id')
        blocked_ids = {right if left == participant.pk else left for left, right in blocks}
        peers, states, conversations, changed = {}, {}, {}, set()
        for match in matches:
            peer = match.partner if match.participant_id == participant.pk else match.participant
            conversation = getattr(match, 'conversation', None)
            if conversation is None:
                continue
            key = str(peer.pk)
            inaccessible = peer.pk in blocked_ids or bool(peer.social_deleted_at) or not peer.user.is_active or bool(peer.active_ban)
            peers[peer.pk] = peer
            states[key] = {'active': match.is_active and not inaccessible and participant.event.state in ['RUNNING', 'PAUSED'], 'blocked': inaccessible}
            conversations[conversation.pk] = key
            if match.created_at >= floor or match.updated_at >= floor or peer.updated_at >= floor or inaccessible:
                changed.add(peer.pk)
        changed.update(ParticipantProfile.objects.filter(participant_id__in=peers, updated_at__gte=floor).values_list('participant_id', flat=True))
        query = Message.objects.filter(conversation_id__in=conversations, updated_at__gte=floor, updated_at__lte=until)
        if after:
            query = query.filter(Q(updated_at__gt=after[0]) | Q(updated_at=after[0], pk__gt=after[1]))
        page = list(query.order_by('updated_at', 'id').values(
            'id', 'body', 'sender_id', 'read_at', 'created_at', 'updated_at', 'conversation_id',
        )[:PAGE_SIZE + 1])
        has_more = len(page) > PAGE_SIZE
        page = page[:PAGE_SIZE]
        unread_conversations = Message.objects.filter(conversation_id__in=conversations, read_at__isnull=True).exclude(sender=participant).values_list('conversation_id', flat=True).distinct()
        unread = sorted({conversations[identifier] for identifier in unread_conversations})
        updates = []
        for peer in EventParticipant.objects.filter(pk__in=changed).select_related('profile', 'user', 'event').prefetch_related('photos'):
            data = person_payload(peer)
            if states[str(peer.pk)]['blocked']:
                data.update(name='Usuário bloqueado', image='/images/profile-placeholder.svg', job='', city='', residenceState='', height=None, gender='', bio='', interests=[], online=False, age=0)
            updates.append(data)
        if has_more:
            last = page[-1]
            cursor = cursor_for(participant, until, floor=floor.isoformat(), after=[last['updated_at'].isoformat(), str(last['id'])])
        else:
            cursor = cursor_for(participant, until)
        status = participant_status(participant)
        if participant.event.state in ['CLOSED', 'ARCHIVED'] and request.query_params.get('state') != participant.event.state:
            status['discoveryReport'] = discovery_report(participant)
        return Response({
            'cursor': cursor, 'hasMore': has_more, 'status': status,
            'messages': [{'peer': conversations[message['conversation_id']], **message_payload(message, participant)} for message in page],
            'chatStates': states, 'peers': updates, 'unread': unread,
            'blocked': [str(identifier) for identifier in blocked_ids],
        })


class ParticipantCatalogView(APIView):
    def get(self, request):
        from apps.profiles.topics import event_topics, topic_payload, available_filter_topics
        participant = current(request)
        topics = event_topics(participant.event)
        filter_topics = available_filter_topics(participant.event, topics)
        metadata = {'profileTopics': topic_payload(topics)}
        if not participant_status(participant)['socialAvailable']:
            return Response({'people': [], 'discovery': [], **metadata})
        people = [person_payload(peer, filter_topics=filter_topics) for peer in visible_participants(participant)]
        preference = ParticipantPreference.objects.filter(participant=participant).first()
        filters = {**DEFAULT_FILTERS, **(preference.filters if preference else {})}
        return Response({'people': people, 'discovery': discovery(participant, filters, people, filter_topics=filter_topics), **metadata})
