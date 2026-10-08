import io
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.apps import apps
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from apps.participants.models import EventParticipant
from apps.matches.models import Match
from apps.messaging.models import Message
from demo.data import demo_id


@override_settings(DEBUG=True, DEMO_USER_PASSWORD="Demo-password-2026!")
class DemoFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=io.StringIO())

    def setUp(self):
        self.client = APIClient()
        self.actor = EventParticipant.objects.get(pk=demo_id("actor"))
        self.client.force_login(self.actor.user)
        session = self.client.session
        session["event_id"] = str(self.actor.event_id)
        session.save()

    def test_seed_is_idempotent_and_preserves_changes(self):
        counts = {m: m.objects.count() for m in apps.get_models()}
        profile = self.actor.profile
        profile.first_name = "Nome alterado"
        profile.save()
        call_command("seed_demo", stdout=io.StringIO())
        profile.refresh_from_db()
        self.assertEqual(profile.first_name, "Nome alterado")
        self.assertEqual(counts, {m: m.objects.count() for m in apps.get_models()})

    @override_settings(DEBUG=False)
    def test_seed_disabled_outside_debug(self):
        count = EventParticipant.objects.count()
        call_command("seed_demo", stdout=io.StringIO())
        self.assertEqual(EventParticipant.objects.count(), count)
        self.assertEqual(self.client.post("/api/auth/register/", {"email": "new@example.com", "password": "somepassword"}).status_code, 403)

    def test_authentication_required(self):
        self.client.logout()
        self.assertEqual(self.client.get("/api/bootstrap/").status_code, 401)

    def test_registration_requires_invite_even_in_debug(self):
        self.client.logout()
        User = apps.get_model("accounts", "User")
        before = User.objects.count()
        response = self.client.post("/api/auth/register/", {
            "email": "no-invite@example.com", "password": "Good-password-2026!",
        }, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.count(), before)
        self.assertFalse(User.objects.filter(email="no-invite@example.com").exists())

    def test_seed_populates_every_domain(self):
        for config in apps.get_app_configs():
            if config.name.startswith("apps."):
                for model in config.get_models():
                    self.assertTrue(model.objects.exists(), model._meta.label)

    def test_profile_filters_and_event_isolation(self):
        data = self.client.get("/api/bootstrap/").json()
        data["profile"]["first"] = "Alex atualizado"
        self.assertEqual(self.client.put("/api/profile/", data["profile"], format="json").status_code, 200)
        response = self.client.put("/api/filters/", {"min": 18, "max": 70, "gender": "Mulheres", "interests": [], "purpose": "Networking"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(p["gender"] == "Mulheres" for p in response.json()["discovery"]))
        historical = demo_id("history.target")
        self.assertEqual(self.client.post(f"/api/interactions/{historical}/", {"decision": "LIKE"}, format="json").status_code, 404)

    def test_profile_saves_and_clears_interests_and_purpose_without_changing_filters(self):
        data = self.client.get('/api/bootstrap/').json()
        profile = {**data['profile'], 'interests': ['Música', 'Tecnologia'], 'purpose': 'Amizade'}
        response = self.client.put('/api/profile/', profile, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.actor.profile.refresh_from_db()
        self.assertEqual(self.actor.profile.interests, profile['interests'])
        self.assertEqual(self.actor.profile.purpose, 'Amizade')
        saved = self.client.get('/api/profile/').json()['profile']
        self.assertEqual(saved['interests'], profile['interests'])
        self.assertEqual(saved['purpose'], 'Amizade')
        self.assertEqual(response.json()['filters'], data['filters'])
        legacy = {key: value for key, value in profile.items() if key not in ['interests', 'purpose']}
        self.assertEqual(self.client.put('/api/profile/', legacy, format='json').status_code, 200)
        self.actor.profile.refresh_from_db()
        self.assertEqual(self.actor.profile.interests, profile['interests'])
        self.assertEqual(self.actor.profile.purpose, 'Amizade')
        response = self.client.put('/api/profile/', {**profile, 'interests': [], 'purpose': ''}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['profile']['interests'], [])
        self.assertEqual(response.json()['profile']['purpose'], '')

    def test_profile_rejects_unknown_interest_and_purpose(self):
        profile = self.client.get('/api/profile/').json()['profile']
        for extra in [{'interests': ['Inválido']}, {'purpose': 'Inválido'}]:
            with self.subTest(extra=extra):
                self.assertEqual(self.client.put('/api/profile/', {**profile, **extra}, format='json').status_code, 400)

    def test_reciprocal_match_message_and_readonly_end(self):
        peer = demo_id("person.1")
        endpoint = f"/api/interactions/{peer}/"
        response = self.client.post(endpoint, {"decision": "LIKE"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()["match"])
        count = Match.objects.count()
        self.client.post(endpoint, {"decision": "LIKE"}, format="json")
        self.assertEqual(Match.objects.count(), count)
        url = f"/api/conversations/{peer}/messages/"
        self.assertEqual(self.client.post(url, {"text": "Mensagem persistida"}, format="json").status_code, 201)
        self.assertTrue(Message.objects.filter(body="Mensagem persistida").exists())
        self.assertEqual(self.client.post(f"/api/matches/{peer}/end/").status_code, 200)
        self.assertEqual(self.client.post(url, {"text": "Não permitida"}, format="json").status_code, 403)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_login_csrf_is_required(self):
        client = APIClient(enforce_csrf_checks=True)
        payload = {"email": self.actor.user.email, "password": "Demo-password-2026!"}
        self.assertEqual(client.post("/api/auth/login/", payload, format="json").status_code, 403)
        token = client.get("/api/session/").json()["csrfToken"]
        self.assertEqual(client.post("/api/auth/login/", payload, format="json", HTTP_X_CSRFTOKEN=token).status_code, 200)

    def test_upload_requires_real_image_and_authenticated_access(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            image = io.BytesIO()
            Image.new("RGB", (10, 10)).save(image, format="PNG")
            upload = SimpleUploadedFile("photo.png", image.getvalue(), content_type="image/png")
            response = self.client.post("/api/profile/photos/", {"file": upload}, format="multipart")
            self.assertEqual(response.status_code, 201)
            url = response.json()["photos"][-1]
            self.assertEqual(self.client.get(url).status_code, 200)
            self.client.logout()
            self.assertEqual(self.client.get(url).status_code, 401)
