from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.organizations.models import Organization
from apps.events.models import Event
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile
from apps.matches.models import Match
from apps.messaging.models import Conversation
from apps.notifications.models import Notification


class MessageNotificationTests(TestCase):
    def test_sent_message_notifies_only_recipient_with_conversation_destination(self):
        event = Event.objects.create(
            organization=Organization.objects.create(name='Client'),
            name='Event', state='RUNNING', mode='ONLINE',
        )
        participants = []
        for name in ['sender', 'recipient', 'other']:
            user = get_user_model().objects.create_user(username=name)
            participant = EventParticipant.objects.create(event=event, user=user, is_active=True)
            ParticipantProfile.objects.create(participant=participant, first_name=name, last_name='Test')
            participants.append(participant)
        sender, recipient, other = participants
        first, second = sorted([sender, recipient], key=lambda p: p.pk.int)
        match = Match.objects.create(participant=first, partner=second)
        Conversation.objects.create(match=match)
        client = APIClient()
        client.force_login(sender.user)
        session = client.session
        session['event_id'] = str(event.pk)
        session.save()
        response = client.post(f'/api/conversations/{recipient.pk}/messages/', {'text': 'Hello'}, format='json')
        self.assertEqual(response.status_code, 201, response.content)
        notice = Notification.objects.get(kind='message')
        self.assertEqual(notice.participant, recipient)
        self.assertEqual(notice.body, 'Hello')
        self.assertEqual(notice.action_path, f'#mensagens?participant={sender.pk}')
        self.assertFalse(Notification.objects.filter(participant__in=[sender, other]).exists())
