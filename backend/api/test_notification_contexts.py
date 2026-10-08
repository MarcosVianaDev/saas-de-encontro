from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.events.models import Event, EventAdministrator
from apps.notifications.models import Notification
from apps.organizations.models import Organization
from apps.participants.models import EventParticipant


class NotificationContextTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='manager-participant', is_superuser=True)
        organization = Organization.objects.create(name='Cliente')
        self.event = Event.objects.create(organization=organization, name='Evento', mode='ONLINE')
        self.other = Event.objects.create(organization=organization, name='Outro', mode='ONLINE')
        self.participant = EventParticipant.objects.create(event=self.event, user=self.user)
        EventAdministrator.objects.create(event=self.event, user=self.user, role='ADMIN')
        self.admin_notice = Notification.objects.create(recipient=self.user, event=self.event, title='Administrativo')
        self.other_admin_notice = Notification.objects.create(recipient=self.user, event=self.other, title='Outro administrativo')
        self.client = APIClient()
        self.client.force_login(self.user)

    def context(self, navigation, event=None):
        session = self.client.session
        session['navigation'] = navigation
        if event:
            session['event_id'] = str(event.pk)
        else:
            session.pop('event_id', None)
        session.save()

    def test_participant_sees_only_own_event_notifications_and_cannot_read_administrative_notices(self):
        notices = [Notification.objects.create(participant=self.participant, event=self.event,
                   title=kind, kind=kind) for kind in ['match', 'like', 'message', 'support', 'announcement']]
        other_participant = EventParticipant.objects.create(event=self.other, user=self.user)
        Notification.objects.create(participant=other_participant, event=self.other, title='Outro evento')
        peer = EventParticipant.objects.create(event=self.event,
            user=get_user_model().objects.create_user(username='peer'))
        Notification.objects.create(participant=peer, event=self.event, title='Privada')
        self.context('participant', self.event)

        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['unread'], len(notices))
        self.assertCountEqual([item['id'] for item in response.json()['items']], [str(n.pk) for n in notices])
        response = self.client.post('/api/notifications/', {'id': str(self.admin_notice.pk)}, format='json')
        self.assertEqual(response.status_code, 404)
        self.admin_notice.refresh_from_db()
        self.assertIsNone(self.admin_notice.read_at)

    def test_administration_sees_only_administrative_notices_for_selected_event(self):
        notice = Notification.objects.create(participant=self.participant, event=self.event, title='Participante')
        self.context('administration', self.event)
        data = self.client.get('/api/notifications/').json()
        self.assertEqual([item['id'] for item in data['items']], [str(self.admin_notice.pk)])
        self.assertEqual(self.client.post('/api/notifications/', {'id': str(notice.pk)}, format='json').status_code, 404)

    def test_global_and_selection_contexts_do_not_expose_participant_notifications(self):
        Notification.objects.create(participant=self.participant, event=self.event, title='Participante')
        self.context('global')
        data = self.client.get('/api/notifications/').json()
        self.assertCountEqual([item['id'] for item in data['items']],
                              [str(self.admin_notice.pk), str(self.other_admin_notice.pk)])
        self.context('selection')
        self.assertEqual(self.client.get('/api/notifications/').json(), {'unread': 0, 'items': []})

    def test_read_participant_notice_is_not_counted_as_unread(self):
        Notification.objects.create(participant=self.participant, title='Aviso lido', read_at=timezone.now())
        self.context('participant', self.event)
        data = self.client.get('/api/notifications/').json()
        self.assertEqual(data['unread'], 0)
        self.assertEqual(len(data['items']), 1)
