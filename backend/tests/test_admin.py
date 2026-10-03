from django.apps import apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from django.test import TestCase
from apps.audit.models import AuditLog
from apps.organizations.models import Organization
from apps.events.models import Event
from apps.participants.models import EventParticipant
from apps.rooms.models import Room, RoomParticipant


class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser("test_admin", password="Test-only-long-password-632!")
        cls.organization = Organization.objects.create(name="Organização")
        cls.event = Event.objects.create(name="Evento", organization=cls.organization)
        cls.participant = EventParticipant.objects.create(event=cls.event, user=cls.superuser)

    def test_every_domain_model_is_registered(self):
        for config in apps.get_app_configs():
            if config.name.startswith("apps."):
                for model in config.get_models():
                    self.assertIn(model, admin.site._registry)

    def test_login_and_all_admin_changelists(self):
        self.assertTrue(self.client.login(username="test_admin", password="Test-only-long-password-632!"))
        self.assertEqual(self.client.get("/admin/").status_code, 200)
        for model in admin.site._registry:
            self.assertEqual(self.client.get(f"/admin/{model._meta.app_label}/{model._meta.model_name}/").status_code, 200)

    def test_anonymous_and_non_staff_cannot_enter(self):
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        get_user_model().objects.create_user("ordinary", password="Test-only-password-321!")
        self.client.login(username="ordinary", password="Test-only-password-321!")
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_participant_cannot_be_added_to_room_of_other_event(self):
        other = Event.objects.create(name="Outro", organization=self.organization)
        room = Room.objects.create(name="Sala", event=other)
        with self.assertRaises(ValidationError):
            RoomParticipant(room=room, participant=self.participant).full_clean()

    def test_participation_is_unique_per_event(self):
        with self.assertRaises(ValidationError):
            EventParticipant(event=self.event, user=self.superuser).full_clean()

    def test_audit_is_append_only_even_for_queryset_mutations(self):
        entry = AuditLog.objects.create(actor=self.superuser, action="test", object_label="event")
        with self.assertRaises(ValidationError):
            entry.save()
        for mutation in (
            lambda: AuditLog.objects.filter(pk=entry.pk).update(action="changed"),
            lambda: AuditLog.objects.filter(pk=entry.pk).delete(),
        ):
            with self.assertRaises(DatabaseError), transaction.atomic():
                mutation()

    def test_audit_admin_is_read_only(self):
        self.client.force_login(self.superuser)
        entry = AuditLog.objects.create(action="test", object_label="event")
        self.assertEqual(self.client.post(f"/admin/audit/auditlog/{entry.pk}/delete/", {"post": "yes"}).status_code, 403)
