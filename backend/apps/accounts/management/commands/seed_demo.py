"""Carga de demonstração somente em DEBUG; atômica e sem sobrescrever cadastros."""
from datetime import timedelta
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from demo.data import FIXTURES, DEMO_EVENT_ID, demo_id


class Command(BaseCommand):
    help = "Cria os dados de demonstração, uma única vez, quando DEBUG=True."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write("DEBUG=False: carga de demonstração ignorada.")
            return
        if not settings.DEMO_USER_PASSWORD:
            raise CommandError("Configure DEMO_USER_PASSWORD no .env para a carga de DEBUG.")
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(2026100301)")
            AuditLog = apps.get_model("audit", "AuditLog")
            if AuditLog.objects.filter(id=demo_id("seed.completed")).exists():
                self.stdout.write("Dados de demonstração já criados; alterações existentes preservadas.")
                return
            self.seed()
        self.stdout.write(self.style.SUCCESS("Demonstração criada: todos os 19 apps populados."))

    def ensure(self, label, key, **values):
        model = apps.get_model(label)
        obj, _ = model.objects.get_or_create(id=demo_id(key), defaults=values)
        return obj

    def user(self, key, email, name, login=False, staff=False):
        User = get_user_model()
        if User.objects.filter(username=email).exclude(id=demo_id(key)).exists():
            raise CommandError("O login da demonstração já pertence a outro usuário; use outro DEMO_USER_EMAIL.")
        user, created = User.objects.get_or_create(id=demo_id(key), defaults={
            "username": email, "email": email, "first_name": name, "last_name": "Demo",
            "is_staff": staff, "is_superuser": staff,
        })
        if created:
            if login:
                user.set_password(settings.DEMO_USER_PASSWORD)
            else:
                user.set_unusable_password()
            user.save()
        self.ensure("accounts.UserProfile", key + ".global", user=user, bio="Perfil global fictício para demonstração.")
        return user

    def participant(self, key, event, user, name, data=None):
        data = data or {}
        participant = self.ensure("participants.EventParticipant", key, event=event, user=user, is_active=True, registration_status='ACTIVE',activated_at=timezone.now(),onboarding_completed_at=timezone.now())
        self.ensure("profiles.ParticipantProfile", key + ".profile", participant=participant,
            first_name=name, last_name="Demo", birth_month=6,
            birth_year=timezone.localdate().year - data.get("age", 28),
            gender=data.get("gender", "Homens"), job=data.get("job", "Participante"),
            interests=data.get("interests", ["Música", "Viagens"]), is_online=data.get("online", True),
            bio="Amo música, viagens e boas conversas. Aqui para conhecer pessoas incríveis e criar boas histórias neste evento!")
        self.ensure("profiles.ParticipantPreference", key + ".preferences", participant=participant,
            filters={"min": 18, "max": 35, "gender": "Todos", "interests": [], "purpose": "Networking", "favorites": []})
        image = data.get("image", "/images/photo-1506794778202-cad84cf45f1d.jpg")
        for position, url in enumerate([image, "/images/photo-1476514525535-07fb3b4ae5f1.jpg", "/images/photo-1470229722913-7c0e2dbbafd3.jpg"]):
            self.ensure("profiles.ParticipantPhoto", key + f".photo.{position}", participant=participant,
                storage_key=url, position=position, is_primary=position == 0, visibility="PRE_MATCH")
        self.ensure("profiles.EventOutfitPhoto", key + ".outfit", participant=participant, storage_key=image)
        if key == 'actor':
            reading=self.ensure('participants.LocationReading','location.reading',participant=participant,latitude=-23.55,longitude=-46.63,accuracy_m=20,distance_m=0,measured_at=timezone.now())
            self.ensure('participants.LocationAnomaly','location.anomaly',participant=participant,reading=reading,criterion='SPEED',resolution='DISCARDED',reason='Exemplo fictício descartado')
            self.ensure('participants.LocationException','location.exception',participant=participant,actor=user,reason='Exemplo fictício expirado',expires_at=timezone.now()-timedelta(days=1))
            thread=self.ensure('notifications.SupportThread','support.thread',participant=participant,subject='Atendimento fictício de demonstração')
            self.ensure('notifications.SupportMessage','support.message',thread=thread,author=user,body='Solicitação fictícia para conhecer o fluxo de suporte.')
            self.ensure('notifications.EventAnnouncement','announcement.draft',event=event,author=user,title='Aviso fictício de demonstração',body='Este aviso permanece como rascunho.')
        return participant

    def seed(self):
        now = timezone.now()
        owner = self.user("user.admin", "admin-demo@eventconnect.local", "Administrador", login=True, staff=True)
        actor = self.user("user.actor", settings.DEMO_USER_EMAIL, "Alex", login=True)
        organization = self.ensure("organizations.Organization", "organization", name="EventConnect Demo", description="Organização fictícia de desenvolvimento.")
        self.ensure("organizations.OrganizationMember", "membership", organization=organization, user=owner)
        event = self.ensure("events.Event", "event.current", organization=organization, name="Conecta São Paulo", description="Demonstração completa do fluxo do participante.", state='RUNNING', opening_origin='manual', opened_at=now, responsible=owner, starts_at=now, ends_at=now + timedelta(days=2))
        assert event.id == DEMO_EVENT_ID
        self.ensure("events.EventAdministrator", "event.admin", event=event, user=owner)
        room = self.ensure("rooms.Room", "room", event=event, name="Encontros e conexões", description="Sala principal da demonstração.")
        self.ensure("rooms.RoomConfiguration", "room.config", room=room, settings={"description": "Sala de demonstração"})
        self.ensure("rooms.RoomAdministrator", "room.admin", room=room, user=owner)
        current = self.participant("actor", event, actor, "Alex")
        self.ensure("rooms.RoomParticipant", "room.actor", room=room, participant=current)
        participants = {}
        for data in FIXTURES["people"]:
            index = data["id"]
            user = self.user(f"user.person.{index}", f"pessoa{index}@eventconnect.local", data["name"])
            target = self.participant(f"person.{index}", event, user, data["name"], data)
            participants[index] = target
            self.ensure("rooms.RoomParticipant", f"room.person.{index}", room=room, participant=target)
            if str(index) in FIXTURES["chats"] or data["mutual"]:
                incoming = self.ensure("interactions.Interaction", f"incoming.{index}", participant=target, target=current, decision="LIKE")
                self.ensure("interactions.InteractionHistory", f"incoming.{index}.history", interaction=incoming, decision="LIKE")
            if str(index) in FIXTURES["chats"]:
                outgoing = self.ensure("interactions.Interaction", f"outgoing.{index}", participant=current, target=target, decision="LIKE")
                self.ensure("interactions.InteractionHistory", f"outgoing.{index}.history", interaction=outgoing, decision="LIKE")
                first, second = sorted([current, target], key=lambda p: p.id.int)
                match = self.ensure("matches.Match", f"match.{index}", participant=first, partner=second)
                conversation = self.ensure("messaging.Conversation", f"conversation.{index}", match=match)
                for number, message in enumerate(FIXTURES["chats"][str(index)]):
                    self.ensure("messaging.Message", f"message.{index}.{number}", conversation=conversation,
                        sender=current if message["mine"] else target, body=message["text"])
        self.ensure("discovery.ProfileDiscovery", "discovery.sample", participant=current, candidate=participants[2])
        field = self.ensure("profiles.ProfileField", "field.interest", name="Interesse principal", event=None)
        self.ensure("profiles.ProfileFieldOption", "field.option", field=field, name="Música")
        self.ensure("profiles.ParticipantFieldValue", "field.value", participant=current, field=field, value={"text": "Música"})
        kind = self.ensure("passes.PassType", "pass.type", name="5 revelações", description="Benefício fictício", reveal_limit=5)
        offer = self.ensure("passes.EventPassOffer", "pass.offer", event=event, pass_type=kind, price="15.00")
        owned = self.ensure("passes.ParticipantPass", "pass.owned", participant=current, offer=offer, expires_at=None)
        self.ensure("passes.PassActivation", "pass.activation", participant_pass=owned, activated_by=owner)
        self.ensure("passes.PassUsage", "pass.usage", participant_pass=owned, revealed_participant=participants[2])
        purchase = self.ensure("payments.PassPurchase", "purchase", participant=current, offer=offer, reference="demo-purchase")
        self.ensure("payments.Payment", "payment", purchase=purchase, amount="15.00", paid_at=now, external_reference="DEMO-SEM-COBRANCA")
        self.ensure("notifications.Notification", "notification", participant=current, title=f"chat:{participants[3].id}", body="Mariana enviou uma mensagem.")
        self.ensure("consent.ConsentRecord", "consent", user=actor, event=event, purpose="Demonstração local", policy_version="demo-1", granted=True)
        self.ensure("analytics.EventMetric", "metric", event=event, name="participantes_demo", value=13, measured_at=now)
        # Exemplos de moderação/governança ficam em outro evento para não bloquear o fluxo principal.
        past = self.ensure("events.Event", "event.history", organization=organization, name="Histórico de demonstração", state='CLOSED', closed_at=now-timedelta(days=6), starts_at=now - timedelta(days=7), ends_at=now - timedelta(days=6))
        old_actor = self.participant("history.actor", past, actor, "Alex")
        sample_user = self.user("user.history", "historico@eventconnect.local", "Exemplo")
        old_target = self.participant("history.target", past, sample_user, "Exemplo")
        past_room = self.ensure("rooms.Room", "history.room", event=past, name="Sala histórica")
        self.ensure("reports.Block", "block", participant=old_actor, target=old_target)
        report = self.ensure("reports.Report", "report", reporter=old_actor, reported=old_target, reason="Relato fictício para inspecionar a moderação no Admin.")
        self.ensure("reports.ReportEvidence", "evidence", report=report, description="Evidência fictícia.")
        case = self.ensure("moderation.ModerationCase", "case", report=report, assigned_to=owner, notes="Exemplo de análise, sem acusação real.")
        self.ensure("moderation.ModerationAction", "action", case=case, actor=owner, description="Registro fictício de providência.")
        self.ensure("moderation.ModerationNote", "note", case=case, author=owner, body="Nota fictícia.")
        self.ensure("moderation.UserSuspension", "suspension", user=sample_user, reason="Exemplo encerrado", ends_at=now - timedelta(days=1))
        self.ensure('moderation.EventSuspension', 'event.suspension', participant=old_target, actor=owner, reason='Exemplo encerrado no evento histórico', ends_at=now - timedelta(days=1))
        self.ensure("moderation.EventBan", "event.ban", participant=old_target, reason="Exemplo de banimento no evento histórico.")
        self.ensure("moderation.RoomBan", "room.ban", room=past_room, participant=old_target, reason="Exemplo histórico.")
        self.ensure("retention.DataRetentionRecord", "retention", participant=old_actor, category="Demonstração; política pendente", scheduled_for=None)
        self.ensure("retention.LegalHold", "hold", participant=old_actor, reason="Exemplo de preservação para inspeção, sem rotina de exclusão.")
        self.ensure("retention.PrivacyRequest", "privacy", user=sample_user, description="Solicitação fictícia para inspeção no Admin.")
        self.ensure("audit.AuditLog", "seed.completed", actor=owner, action="demo.seed.completed", object_label="events.Event", object_id=event.id, details={"fixture_version": 1})
