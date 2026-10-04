import io
from datetime import timedelta
from unittest.mock import patch
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase,override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from apps.events.models import Event,EventAdministrator
from apps.events.services import transition
from apps.participants.models import EventParticipant,LocationReading,LocationAnomaly
from apps.participants.location import reading,failed,exception
from apps.profiles.models import ParticipantPhoto,EventOutfitPhoto,ProfileField,ParticipantFieldValue
from apps.reports.models import Report,Block
from apps.moderation.models import ModerationCase
from apps.notifications.models import Notification,EventAnnouncement
from apps.notifications.announcements import send,dispatch_due
from apps.passes.models import PassType,EventPassOffer,ParticipantPass,PassUsage
from apps.passes.services import expire_passes
from apps.audit.models import AuditLog
from apps.accounts.models import UserProfile
from apps.interactions.models import Interaction
from demo.data import demo_id


@override_settings(DEBUG=True,DEMO_USER_PASSWORD='Demo-password-2026!')
class MvpFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo',stdout=io.StringIO())
        cls.event=Event.objects.get(pk=demo_id('event.current'))
        cls.actor=EventParticipant.objects.get(pk=demo_id('actor'))
        cls.peer=EventParticipant.objects.get(pk=demo_id('person.1'))
        cls.global_user=get_user_model().objects.get(email='admin-demo@eventconnect.local')
        cls.manager=get_user_model().objects.create_user(username='manager',email='manager@example.com',password='Pass-long-2026!')
        cls.moderator=get_user_model().objects.create_user(username='moderator',email='moderator@example.com')
        cls.operator=get_user_model().objects.create_user(username='operator',email='operator@example.com')
        EventAdministrator.objects.create(event=cls.event,user=cls.manager,role='ADMIN')
        EventAdministrator.objects.create(event=cls.event,user=cls.moderator,role='MODERATOR')
        EventAdministrator.objects.create(event=cls.event,user=cls.operator,role='OPERATOR',permissions=['passes'])

    def setUp(self):
        self.client=APIClient();self.as_user(self.actor.user)

    def as_user(self,user):
        self.client.force_login(user);s=self.client.session;s['event_id']=str(self.event.pk);s['navigation']='participant';s.save()

    def state(self,state):
        Event.objects.filter(pk=self.event.pk).update(state=state)
        self.event.refresh_from_db()

    def test_superuser_global_staff_does_not_grant_global_context(self):
        self.as_user(self.global_user)
        self.assertEqual(self.client.get('/api/global/').status_code,200)
        staff=get_user_model().objects.create_user(username='staff',is_staff=True)
        self.as_user(staff)
        self.assertEqual(self.client.get('/api/global/').status_code,403)
        self.assertFalse(any(c['navigation']=='global' for c in self.client.get('/api/contexts/').json()['contexts']))

    def test_context_selection_checks_membership_and_preserves_shared_identity(self):
        self.as_user(self.global_user)
        self.assertEqual(self.client.post('/api/global/event/',{'event':str(self.event.pk)},format='json').status_code,200)
        self.assertTrue(self.client.get('/api/event-admin/').json()['globalContext'])
        self.as_user(self.actor.user)
        self.assertEqual(self.client.post('/api/contexts/',{'key':'global'},format='json').status_code,403)
        r=self.client.post('/api/contexts/',{'key':f'participant:{self.event.pk}'},format='json')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()['event']['id'],str(self.event.pk))

    def test_guided_client_draft_activation_is_atomic_and_idempotent(self):
        self.as_user(self.global_user)
        payload={'contact':'Contato fictício','email':'contact@example.com','organization':'Cliente novo',
            'event':'Evento novo','starts':(timezone.now()+timedelta(days=1)).isoformat(),
            'ends':(timezone.now()+timedelta(days=2)).isoformat(),'responsible':self.manager.email}
        r=self.client.post('/api/global/',payload,format='json');self.assertEqual(r.status_code,200)
        org_id=r.json()['id'];payload.update(id=org_id,activate=True)
        for _ in range(2):self.assertEqual(self.client.post('/api/global/',payload,format='json').status_code,200)
        event=Event.objects.get(organization_id=org_id);self.assertEqual(event.state,'SCHEDULED')
        self.assertEqual(event.administrators.get().user,self.manager)

    def test_delegation_reclaim_and_permission_boundaries(self):
        self.as_user(self.manager)
        r=self.client.post('/api/event-admin/team/',{'action':'delegate','id':str(EventAdministrator.objects.get(event=self.event,user=self.moderator).pk),'confirmed':True},format='json')
        self.assertEqual(r.status_code,200)
        self.assertEqual(self.client.get('/api/event-admin/').json()['role'],'DELEGATED')
        self.assertEqual(self.client.get('/api/event-admin/team/').status_code,403)
        self.as_user(self.moderator)
        self.assertEqual(self.client.get('/api/event-admin/').json()['role'],'ADMIN')
        self.as_user(self.manager)
        self.assertEqual(self.client.post('/api/event-admin/team/',{'action':'reclaim'},format='json').status_code,200)
        self.as_user(self.moderator)
        self.assertEqual(self.client.get('/api/event-admin/financial/').status_code,403)
        self.assertTrue(AuditLog.objects.filter(action='team.delegated').exists())

    def test_operator_can_open_occurrence_without_moderation_privileges(self):
        self.as_user(self.operator)
        endpoint=f'/api/event-admin/participants/{self.peer.pk}/action/'
        self.assertEqual(self.client.post(endpoint,{'action':'report','reason':'Passe não vigorou'},format='json').status_code,200)
        self.assertEqual(self.client.post(endpoint,{'action':'suspend','reason':'Exemplo'},format='json').status_code,403)

    def test_paused_blocks_social_but_allows_existing_messages(self):
        # Seed peer 2 has an existing reciprocal match with the actor.
        self.state('PAUSED')
        self.assertEqual(self.client.get('/api/discovery/').status_code,403)
        self.assertEqual(self.client.get('/api/participants/').status_code,403)
        self.assertEqual(self.client.post(f'/api/interactions/{self.peer.pk}/',{'decision':'LIKE'},format='json').status_code,403)
        peer=demo_id('person.2')
        self.assertEqual(self.client.post(f'/api/conversations/{peer}/messages/',{'text':'Mensagem durante pausa'},format='json').status_code,201)

    def test_closed_event_read_only_and_global_profile_disposition(self):
        self.state('CLOSED')
        data=self.client.get('/api/bootstrap/').json()
        self.assertTrue(data['event']['readOnly']);self.assertFalse(data['discovery'])
        self.assertEqual(self.client.put('/api/profile/',data['profile'],format='json').status_code,403)
        self.assertEqual(self.client.put('/api/filters/',data['filters'],format='json').status_code,403)
        peer=demo_id('person.2')
        self.assertEqual(self.client.post(f'/api/conversations/{peer}/messages/',{'text':'Bloqueada'},format='json').status_code,403)
        self.assertEqual(self.client.get(f'/api/conversations/{peer}/messages/').status_code,200)
        self.assertEqual(self.client.post('/api/profile/disposition/',{'action':'persist'},format='json').status_code,200)
        self.assertTrue(UserProfile.objects.get(user=self.actor.user).preferences['event_profile'])
        self.assertEqual(self.client.post('/api/profile/disposition/',{'action':'delete','confirmed':True},format='json').status_code,200)
        self.actor.refresh_from_db();self.assertIsNotNone(self.actor.social_deleted_at)
        self.assertTrue(self.actor.photos.exists())

    def test_public_photos_immutable_after_activation(self):
        data=self.client.get('/api/bootstrap/').json()
        self.assertEqual(self.client.delete('/api/profile/photos/',{'url':data['photos'][0]},format='json').status_code,403)
        self.assertEqual(self.actor.photos.filter(removed_at__isnull=True).count(),3)

    def test_activation_requires_outfit_three_public_photos_and_event_fields(self):
        self.as_user(self.operator)
        endpoint=f'/api/event-admin/participants/{self.peer.pk}/activate/'
        self.assertEqual(self.client.post(endpoint,{},format='json').status_code,200)
        EventOutfitPhoto.objects.filter(participant=self.peer).delete()
        self.assertEqual(self.client.post(endpoint,{},format='json').status_code,400)

    def test_favorite_only_after_match(self):
        self.assertEqual(self.client.post(f'/api/favorites/{self.peer.pk}/',{},format='json').status_code,404)
        self.assertEqual(self.client.post(f'/api/favorites/{demo_id("person.2")}/',{},format='json').status_code,200)

    def test_block_anonymizes_conversation_without_creating_report(self):
        peer=demo_id('person.2');count=Report.objects.count()
        response=self.client.post(f'/api/blocks/{peer}/',{'confirmed':True,'reason':'Não quero interagir'},format='json')
        self.assertEqual(response.status_code,200)
        person=next(p for p in response.json()['people'] if p['id']==str(peer))
        self.assertEqual(person['name'],'Usuário bloqueado')
        self.assertEqual(Report.objects.count(),count)
        self.assertFalse(response.json()['chatStates'][str(peer)]['active'])

    def test_report_thresholds_ignore_unfounded_and_do_not_ban(self):
        endpoint=f'/api/reports/{self.peer.pk}/'
        payload={'reasons':['Outro'],'description':'Relato fictício para análise'}
        for _ in range(10):self.assertEqual(self.client.post(endpoint,payload,format='json').status_code,201)
        self.peer.refresh_from_db();self.assertTrue(self.peer.is_active)
        self.assertTrue(Notification.objects.filter(kind='reports10').exists())
        report=Report.objects.filter(reported=self.peer,description=payload['description']).first()
        case=ModerationCase.objects.get(report=report)
        self.as_user(self.moderator)
        self.assertEqual(self.client.post(f'/api/event-admin/cases/{case.pk}/action/',{'action':'resolve','reason':'Denúncia revisada e considerada infundada','unfounded':True},format='json').status_code,200)
        report.refresh_from_db();self.assertTrue(report.is_unfounded)
        self.as_user(self.actor.user)
        for _ in range(10):self.client.post(endpoint,payload,format='json')
        self.peer.refresh_from_db();self.assertTrue(self.peer.is_active)
        self.client.post(endpoint,payload,format='json')
        self.peer.refresh_from_db();self.assertFalse(self.peer.is_active)
        self.assertEqual(self.peer.deactivation_reason,'REPORT_REVIEW')
        self.assertFalse(hasattr(self.peer,'ban'))
        self.assertTrue(Notification.objects.filter(kind='reports20',recipient=self.global_user).exists())

    def test_reports_cross_event_evidence_rejected_and_rolled_back(self):
        foreign=ParticipantPhoto.objects.filter(participant__event__state='CLOSED').first()
        count=Report.objects.count()
        r=self.client.post(f'/api/reports/{self.peer.pk}/',{'reasons':['Outro'],'description':'Relato','evidence':{'photo':str(foreign.pk)}},format='json')
        self.assertEqual(r.status_code,404);self.assertEqual(Report.objects.count(),count)

    def test_manual_pass_grant_revoke_preserves_financial_snapshot(self):
        offer=EventPassOffer.objects.create(event=self.event,pass_type=PassType.objects.create(name='10 revelações',reveal_limit=10),price=Decimal('20'))
        self.as_user(self.operator)
        payload={'offer':str(offer.pk),'participant':str(self.actor.pk),'origin':'Balcão','reference':'Venda declarada'}
        self.assertEqual(self.client.post('/api/event-admin/passes/',payload,format='json').status_code,200)
        p=ParticipantPass.objects.get(participant=self.actor,offer=offer)
        self.assertEqual(p.sale_amount,Decimal('20'))
        self.assertEqual(self.client.post('/api/event-admin/passes/',{'action':'revoke','id':str(p.pk),'reason':'Correção'},format='json').status_code,200)
        p.refresh_from_db();self.assertEqual(p.sale_amount,Decimal('20'));self.assertIsNotNone(p.revoked_at)
        self.as_user(self.manager)
        self.assertTrue(any(s['id']==str(p.pk) and s['amount']=='20.00' for s in self.client.get('/api/event-admin/financial/').json()['sales']))

    def test_likes_hidden_and_reveal_oldest_consumes_once(self):
        ParticipantPass.objects.filter(participant=self.actor).update(revoked_at=timezone.now())
        PassUsage.objects.filter(participant_pass__participant=self.actor).delete()
        # Ensure the hidden oldest peer is in the eligible pool and not yet matched.
        first=self.client.get('/api/likes-received/').json();self.assertGreater(first['hidden'],0);self.assertFalse(first['people'])
        self.assertEqual(self.client.post('/api/likes-received/',{},format='json').status_code,400)
        offer=EventPassOffer.objects.create(event=self.event,pass_type=PassType.objects.create(name='Uma revelação',reveal_limit=1),price=0)
        p=ParticipantPass.objects.create(participant=self.actor,offer=offer,reveal_limit=1)
        r=self.client.post('/api/likes-received/',{},format='json');self.assertEqual(r.status_code,200);self.assertEqual(r.json()['remaining'],0)
        self.assertEqual(self.client.post('/api/likes-received/',{},format='json').status_code,400)
        self.assertEqual(p.usages.count(),1)

    def test_pass_expiry_idempotent_and_likes_preserved(self):
        offer=EventPassOffer.objects.create(event=self.event,pass_type=PassType.objects.create(name='Temporal',duration=timedelta(minutes=1)),price=0)
        p=ParticipantPass.objects.create(participant=self.actor,offer=offer,expires_at=timezone.now()-timedelta(seconds=1))
        count=Interaction.objects.count();expire_passes();expire_passes()
        self.assertEqual(Notification.objects.filter(dedupe_key=f'pass-expired:{p.pk}').count(),1)
        self.assertEqual(Interaction.objects.count(),count)

    def physical(self):
        Event.objects.filter(pk=self.event.pk).update(mode='PHYSICAL',latitude=-23.55,longitude=-46.63,location_interval_minutes=15)
        self.event.refresh_from_db();self.actor.refresh_from_db();return self.actor

    def test_geolocation_presence_outside_and_technical_recovery(self):
        p=self.physical();now=timezone.now()
        p=reading(p,{'latitude':-23.55,'longitude':-46.63,'accuracy':20},now)
        self.assertEqual(p.presence,'PRESENT')
        p=reading(p,{'latitude':-23.5365,'longitude':-46.63},now+timedelta(minutes=15))
        self.assertEqual(p.presence,'OUTSIDE');self.assertTrue(p.is_active)
        p=failed(p,now=now+timedelta(minutes=16))
        for i in range(5):p=failed(p,'retry',now+timedelta(minutes=17+i))
        self.assertTrue(p.is_active);self.assertEqual(p.location_retry_count,5)
        p=failed(p,'periodic',now+timedelta(minutes=31))
        self.assertFalse(p.is_active);self.assertEqual(p.deactivation_reason,'GPS_TECHNICAL')
        p=reading(p,{'latitude':-23.55,'longitude':-46.63},now+timedelta(minutes=32))
        self.assertTrue(p.is_active);self.assertEqual(p.deactivation_reason,'')

    def test_location_denial_keeps_messages_and_anomaly_never_sanctions(self):
        p=self.physical()
        self.assertEqual(self.client.post('/api/location/',{'action':'deny'},format='json').status_code,200)
        self.assertEqual(self.client.get('/api/discovery/').status_code,403)
        self.assertEqual(self.client.post(f'/api/conversations/{demo_id("person.2")}/messages/',{'text':'Ainda posso conversar'},format='json').status_code,201)
        now=timezone.now();reading(p,{'latitude':-23.55,'longitude':-46.63},now)
        reading(p,{'latitude':-24.55,'longitude':-46.63},now+timedelta(minutes=1))
        p=reading(p,{'latitude':-24.55,'longitude':-46.63},now+timedelta(minutes=2))
        self.assertTrue(p.is_active);self.assertTrue(LocationAnomaly.objects.filter(participant=p,criterion='DISTANCE').exists())

    def test_location_history_restricted_by_role_state_and_requires_audit(self):
        self.physical();endpoint=f'/api/event-admin/participants/{self.actor.pk}/location-history/'
        self.as_user(self.manager)
        self.assertEqual(self.client.post(endpoint,{'reason':'Investigação'},format='json').status_code,403)
        self.state('PAUSED')
        self.assertEqual(self.client.post(endpoint,{},format='json').status_code,400)
        self.assertEqual(self.client.post(endpoint,{'reason':'Investigação'},format='json').status_code,200)
        self.assertTrue(AuditLog.objects.filter(action='location.history_viewed').exists())
        self.as_user(self.moderator)
        self.assertEqual(self.client.post(endpoint,{'reason':'Não autorizado'},format='json').status_code,403)

    def test_location_exception_is_audited_and_not_punitive(self):
        p=self.physical();p.is_active=False;p.deactivation_reason='GPS_TECHNICAL';p.save()
        self.as_user(self.moderator)
        response=self.client.post(f'/api/event-admin/participants/{p.pk}/location-exception/',{'minutes':15,'reason':'Falha no dispositivo'},format='json')
        self.assertEqual(response.status_code,200)
        p.refresh_from_db();self.assertTrue(p.is_active);self.assertTrue(p.location_exceptions.exists())
        self.assertFalse(hasattr(p,'ban'))

    def test_notifications_are_private_and_marking_read_does_not_leak(self):
        n=Notification.objects.create(participant=self.peer,event=self.event,title='Privada')
        response=self.client.get('/api/notifications/').json()
        self.assertNotIn(str(n.pk),[item['id'] for item in response['items']])
        self.assertEqual(self.client.post('/api/notifications/',{'id':str(n.pk)},format='json').status_code,404)

    def test_scheduled_announcements_revalidate_pause_and_close_and_are_idempotent(self):
        self.as_user(self.moderator)
        data={'title':'Aviso','body':'Conteúdo','action':'schedule','scheduled':(timezone.now()+timedelta(minutes=1)).isoformat()}
        r=self.client.post('/api/event-admin/announcements/',data,format='json');self.assertEqual(r.status_code,200)
        a=EventAnnouncement.objects.get(pk=r.json()['id'])
        self.state('PAUSED');dispatch_due(timezone.now()+timedelta(minutes=2));a.refresh_from_db();self.assertEqual(a.state,'HELD')
        send(a,actor=self.moderator);send(a,actor=self.moderator)
        self.assertEqual(Notification.objects.filter(dedupe_key__startswith=f'announcement:{a.pk}:').count(),self.event.participants.count())
        b=EventAnnouncement.objects.create(event=self.event,author=self.moderator,title='Tarde',body='Não enviar',state='SCHEDULED',scheduled_at=timezone.now())
        self.state('CLOSED');dispatch_due();b.refresh_from_db();self.assertEqual(b.state,'CANCELLED')

    def test_announcement_last_thirty_minutes_and_end_validation(self):
        self.as_user(self.moderator);data={'title':'Aviso','body':'Conteúdo','action':'schedule'}
        data['scheduled']=(self.event.ends_at-timedelta(minutes=15)).isoformat()
        self.assertEqual(self.client.post('/api/event-admin/announcements/',data,format='json').status_code,400)
        data['confirmed']=True;self.assertEqual(self.client.post('/api/event-admin/announcements/',data,format='json').status_code,200)
        data['scheduled']=(self.event.ends_at+timedelta(seconds=1)).isoformat()
        self.assertEqual(self.client.post('/api/event-admin/announcements/',data,format='json').status_code,400)

    def test_support_request_reply_and_event_isolation(self):
        r=self.client.post('/api/support/',{'body':'Preciso de ajuda com o perfil'},format='json');self.assertEqual(r.status_code,201)
        thread=r.json()['id'];self.as_user(self.moderator)
        self.assertEqual(self.client.post('/api/event-admin/support/',{'thread':thread,'body':'Vamos ajudar'},format='json').status_code,201)
        self.as_user(self.peer.user)
        self.assertEqual(self.client.post('/api/support/',{'thread':thread,'body':'Não autorizado'},format='json').status_code,404)

    def test_message_read_state_persists_and_inactive_gps_peer_can_receive(self):
        from apps.messaging.models import Message
        peer=EventParticipant.objects.get(pk=demo_id('person.2'))
        peer.is_active=False;peer.registration_status='INACTIVE';peer.deactivation_reason='GPS_TECHNICAL';peer.save()
        endpoint=f'/api/conversations/{peer.pk}/messages/'
        r=self.client.post(endpoint,{'text':'Mensagem durante falha técnica'},format='json')
        self.assertEqual(r.status_code,201)
        message=Message.objects.get(body='Mensagem durante falha técnica')
        self.as_user(peer.user)
        data=self.client.get('/api/conversations/').json()
        self.assertTrue(any(m['unread'] for m in data['chats'][str(self.actor.pk)]))
        self.assertEqual(self.client.get(f'/api/conversations/{self.actor.pk}/messages/').status_code,200)
        message.refresh_from_db();self.assertIsNotNone(message.read_at)
        self.assertFalse(any(m['unread'] for m in self.client.get('/api/conversations/').json()['chats'][str(self.actor.pk)]))

    def test_outfit_content_requires_event_and_active_match(self):
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage
        key=default_storage.save('tests/outfit.txt',ContentFile(b'outfit'))
        self.addCleanup(default_storage.delete,key)
        peer=EventParticipant.objects.get(pk=demo_id('person.2'))
        EventOutfitPhoto.objects.filter(participant=peer).update(storage_key=key)
        self.assertEqual(self.client.get(f'/api/outfits/{peer.pk}/content/').status_code,200)
        self.assertEqual(self.client.get(f'/api/outfits/{self.peer.pk}/content/').status_code,404)
        self.client.post(f'/api/blocks/{peer.pk}/',{'confirmed':True},format='json')
        self.assertEqual(self.client.get(f'/api/outfits/{peer.pk}/content/').status_code,403)

    def test_profile_removal_preserves_history_requires_origin_and_allows_replacement(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.core.files.storage import default_storage
        from PIL import Image
        self.as_user(self.peer.user)
        thread=self.client.post('/api/support/',{'body':'Solicito revisão de uma foto'},format='json').json()['id']
        self.as_user(self.moderator)
        photo=self.peer.photos.filter(visibility='PRE_MATCH',is_primary=True).get()
        endpoint=f'/api/event-admin/participants/{self.peer.pk}/profile-intervention/'
        data={'action':'remove_photo','photo':str(photo.pk),'reason':'Revisão solicitada','kind':'support'}
        data['source']=self.actor.support_threads.first().pk
        self.assertEqual(self.client.post(endpoint,data,format='json').status_code,404)
        data['source']=thread;self.assertEqual(self.client.post(endpoint,data,format='json').status_code,200)
        photo.refresh_from_db();self.assertIsNotNone(photo.removed_at)
        self.peer.refresh_from_db();self.assertFalse(self.peer.is_active)
        self.as_user(self.peer.user)
        content=io.BytesIO();Image.new('RGB',(10,10)).save(content,format='PNG')
        response=self.client.post('/api/profile/photos/',{'file':SimpleUploadedFile('new.png',content.getvalue(),content_type='image/png')},format='multipart')
        self.assertEqual(response.status_code,201)
        replacement=self.peer.photos.order_by('-created_at').first();self.addCleanup(default_storage.delete,replacement.storage_key)
        self.assertEqual(replacement.visibility,'PRE_MATCH');self.assertTrue(replacement.is_primary)
        self.as_user(self.operator)
        self.assertEqual(self.client.post(f'/api/event-admin/participants/{self.peer.pk}/activate/',{},format='json').status_code,200)

    def test_exception_expiry_deactivates_only_unrecovered_gps_failure(self):
        from apps.participants.location import expire_exceptions
        now=timezone.now();self.actor.deactivation_reason='GPS_TECHNICAL';self.actor.is_active=False;self.actor.save()
        exception(self.actor,self.moderator,1,'Aparelho indisponível',now)
        self.assertEqual(expire_exceptions(now+timedelta(minutes=2)),1)
        self.actor.refresh_from_db();self.assertFalse(self.actor.is_active)
        self.assertEqual(expire_exceptions(now+timedelta(minutes=3)),0)

    def test_report_evidence_choices_exclude_post_match_photos_and_store_message_snapshot(self):
        from apps.messaging.models import Message
        from apps.reports.models import ReportEvidence
        from .social_safety import REASONS
        private=ParticipantPhoto.objects.create(participant=self.peer,storage_key='private',position=5,visibility='POST_MATCH')
        choices=self.client.get(f'/api/reports/{self.peer.pk}/').json()
        self.assertNotIn(str(private.pk),[p['id'] for p in choices['photos']])
        message=Message.objects.filter(sender__event=self.event,conversation__match__partner=self.actor).first()
        if not message:message=Message.objects.filter(conversation__match__participant=self.actor).first()
        match=message.conversation.match;peer=match.partner if match.participant_id==self.actor.pk else match.participant
        response=self.client.post(f'/api/reports/{peer.pk}/',{'reasons':[REASONS[0]],'description':'Relato com mensagem','evidence':{'message':str(message.pk)}},format='json')
        self.assertEqual(response.status_code,201)
        self.assertTrue(ReportEvidence.objects.filter(snapshot__message=str(message.pk),snapshot__body=message.body).exists())

    def test_recurrence_is_global_manual_and_join_never_auto_bans(self):
        from .event_admin import join_event
        profile=self.actor.user.profile
        self.as_user(self.moderator)
        data={'action':'recurrence','profile':str(profile.pk),'marked':True,'reason':'Histórico revisado','confirmed':True}
        self.assertEqual(self.client.post('/api/global/',data,format='json').status_code,403)
        self.as_user(self.global_user)
        self.assertEqual(self.client.post('/api/global/',data,format='json').status_code,200)
        profile.refresh_from_db();self.assertTrue(profile.recurring_reported)
        new=Event.objects.create(organization=self.event.organization,name='Novo evento fictício',state='OPEN',starts_at=timezone.now(),ends_at=timezone.now()+timedelta(hours=2))
        p=join_event(self.actor.user,new)
        self.assertFalse(hasattr(p,'ban'))
        self.assertTrue(Notification.objects.filter(recipient=self.global_user,event=new,title__contains='acompanhamento').exists())
        self.assertEqual(self.client.get('/api/global/').status_code,200)

    def test_location_decision_requires_paused_manager_and_preserves_revoked_ban(self):
        from apps.moderation.models import EventBan
        point=LocationReading.objects.create(participant=self.peer,latitude=0,longitude=0,accuracy_m=10,distance_m=3000,measured_at=timezone.now(),anomalous=True)
        anomaly=LocationAnomaly.objects.create(participant=self.peer,reading=point,criterion='DISTANCE')
        endpoint=f'/api/event-admin/participants/{self.peer.pk}/location-decision/'
        data={'anomaly':str(anomaly.pk),'resolution':'EVENT_BAN','reason':'Investigação concluída','confirmed':True}
        self.as_user(self.manager);self.assertEqual(self.client.post(endpoint,data,format='json').status_code,403)
        self.state('PAUSED');self.as_user(self.moderator)
        self.assertEqual(self.client.post(endpoint,data,format='json').status_code,403)
        self.as_user(self.manager);self.assertEqual(self.client.post(endpoint,data,format='json').status_code,200)
        ban=EventBan.objects.get(participant=self.peer);self.assertEqual(ban.location_anomaly,anomaly)
        self.peer.refresh_from_db();self.assertIsNotNone(self.peer.active_ban)
        data.update(resolution='REVOKE_BAN',reason='Informações adicionais revisadas')
        self.assertEqual(self.client.post(endpoint,data,format='json').status_code,200)
        ban.refresh_from_db();self.assertIsNotNone(ban.revoked_at);self.assertEqual(ban.revoked_by,self.manager)
        self.peer.refresh_from_db();self.assertIsNone(self.peer.active_ban)
        self.assertEqual(AuditLog.objects.filter(action='location.decision',object_id=anomaly.pk).count(),2)

    def test_early_closed_event_removes_invite_and_nonmanager_metrics(self):
        self.state('CLOSED');self.as_user(self.manager)
        data=self.client.get('/api/event-admin/').json();self.assertIsNone(data['event']['joinPath'])
        self.as_user(self.moderator);data=self.client.get('/api/event-admin/').json()
        self.assertTrue(all(value is None for value in data['metrics'].values()))

    def test_offer_edit_does_not_change_existing_sales_or_entitlements(self):
        self.state('OPEN')
        offer=EventPassOffer.objects.create(event=self.event,pass_type=PassType.objects.create(name='Original',reveal_limit=10),price=Decimal('12.00'))
        self.as_user(self.operator)
        self.assertEqual(self.client.post('/api/event-admin/passes/',{'participant':str(self.actor.pk),'offer':str(offer.pk),'origin':'Teste'},format='json').status_code,200)
        issued=ParticipantPass.objects.get(participant=self.actor,offer=offer)
        self.as_user(self.manager)
        data={'action':'offer','id':str(offer.pk),'name':'Atualizada','price':'25.00','limit':20,'minutes':0}
        self.assertEqual(self.client.post('/api/event-admin/passes/',data,format='json').status_code,200)
        issued.refresh_from_db();offer.refresh_from_db()
        self.assertEqual(issued.offer_name,'Original');self.assertEqual(issued.sale_amount,Decimal('12.00'));self.assertEqual(issued.reveal_limit,10)
        self.assertEqual(offer.price,Decimal('25.00'));self.assertEqual(offer.pass_type.reveal_limit,20)
        self.state('RUNNING');self.assertEqual(self.client.post('/api/event-admin/passes/',data,format='json').status_code,403)

    def test_payment_instructions_are_global_only_and_freeze_at_start(self):
        self.state('OPEN');endpoint='/api/event-admin/configuration/'
        data={'pass_payment_instructions':'Ative o passe no atendimento identificado do evento.'}
        self.as_user(self.manager);self.assertEqual(self.client.put(endpoint,data,format='json').status_code,403)
        self.as_user(self.global_user);self.assertEqual(self.client.put(endpoint,data,format='json').status_code,200)
        self.state('RUNNING');self.as_user(self.actor.user)
        self.assertEqual(self.client.get('/api/likes-received/').json()['instructions'],data['pass_payment_instructions'])
        self.as_user(self.global_user);self.assertEqual(self.client.put(endpoint,data,format='json').status_code,403)
