import uuid
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.storage import default_storage
from django.db import transaction, IntegrityError
from django.http import FileResponse, Http404
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.models import UserProfile
from apps.events.models import Event
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ParticipantPreference, ParticipantPhoto, ParticipantFieldValue
from apps.messaging.models import Message
from demo.data import DEMO_EVENT_ID
from .serializers import LoginSerializer, ProfileSerializer, FilterSerializer, DecisionSerializer, MessageSerializer, PhotoDeleteSerializer
from .services import current, bootstrap, target_for, blocked, visible_participants, match_for, photo_url, ordered_photos, person_payload, record_decision, audit, DEFAULT_FILTERS
from .event_admin import navigation, invite_event, join_event
from .services import ensure_social, ensure_writable


def login_payload(request):
    if request.session.get('navigation') == 'selection':
        from .contexts import administration_context, select
        context = administration_context(request.user)
        if context:
            select(request, context['key'])
    nav = navigation(request)
    if request.session.get('navigation') == 'participant':
        nav = {'navigation': 'participant'}
    if nav['navigation'] in ['administration','global','selection']:
        return nav
    return {**bootstrap(current(request)), **nav}


class SessionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        authenticated = request.user.is_authenticated
        return Response({"authenticated": authenticated, "csrfToken": get_token(request),
            "demoEmail": settings.DEMO_USER_EMAIL if settings.DEBUG else None})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = authenticate(request, username=data["email"].lower(), password=data["password"])
        if user is None:
            raise ValidationError("E-mail ou senha inválidos.")
        token = request.data.get('invite')
        member = user.event_administrations.filter(is_active=True).order_by('created_at').first()
        if request.data.get('event') is not None and not token:
            raise ValidationError("O UUID do evento deve acompanhar um convite válido.")
        participant = join_event(user, invite_event(token, request.data.get('event'))) if token else user.event_participations.filter(event_id=DEMO_EVENT_ID).first() or user.event_participations.order_by("created_at").first()
        if participant is None and member is None and not user.is_superuser:
            raise PermissionDenied("Esta conta não participa de um evento.")
        login(request, user)
        from .contexts import available, select
        contexts = available(user)
        if token:
            request.session['navigation'] = 'participant'; request.session['event_id'] = str(participant.event_id)
        elif any(context['navigation'] in ['global', 'administration'] for context in contexts):
            select(request, next(context['key'] for context in contexts if context['navigation'] in ['global', 'administration']))
        elif len(contexts) > 1:
            request.session['navigation'] = 'selection'; request.session.pop('event_id',None)
        else:
            select(request,contexts[0]['key'])
        return Response({"csrfToken": get_token(request), "data": login_payload(request)})


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        token = request.data.get('invite')
        if not token:
            raise PermissionDenied("O cadastro de participantes exige um convite de evento. Contas de gestão devem ser criadas no Django Admin.")
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            validate_password(data["password"])
        except DjangoValidationError as error:
            raise ValidationError({"password": error.messages})
        event = invite_event(token, request.data.get('event'))
        try:
            with transaction.atomic():
                user = get_user_model().objects.create_user(username=data["email"].lower(), email=data["email"].lower(), password=data["password"])
                UserProfile.objects.create(user=user)
                participant = join_event(user, event)
                audit(user, "account.registered", user)
        except IntegrityError:
            raise ValidationError("Este e-mail já está cadastrado.")
        login(request, user)
        request.session["event_id"] = str(event.id)
        request.session['navigation'] = 'participant'
        return Response({"csrfToken": get_token(request), "data": {**bootstrap(participant), 'navigation': 'participant'}}, status=201)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"csrfToken": get_token(request)})


class BootstrapView(APIView):
    def get(self, request):
        return Response(login_payload(request))


class ProfileView(APIView):
    def get(self, request):
        data = bootstrap(current(request))
        return Response({key: data[key] for key in ["profile", "photos", "active"]})

    def put(self, request):
        serializer = ProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            participant = current(request)
            ensure_writable(participant)
            EventParticipant.objects.select_for_update().get(pk=participant.pk)
            photos = ordered_photos(participant)
            if not 3 <= len(photos) <= 10 or len([p for p in photos if p.visibility == "PRE_MATCH"]) != 3 or len([p for p in photos if p.is_primary]) != 1:
                raise ValidationError("São necessárias 3 fotos públicas e uma principal para ativar o perfil.")
            for field in participant.event.profile_fields.filter(is_required=True):
                if not ParticipantFieldValue.objects.filter(participant=participant, field=field).exclude(value={}).exists():
                    raise ValidationError(f"Preencha o campo obrigatório: {field.name}.")
            profile = participant.profile
            for source, target in {"first": "first_name", "last": "last_name", "month": "birth_month", "year": "birth_year", "gender": "gender", "bio": "bio"}.items():
                setattr(profile, target, data[source])
            profile.full_clean()
            profile.save()
            from .profile_operations import validate_activation
            if participant.event.auto_activate_participants:
                validate_activation(participant)
                if not participant.is_active and not participant.deactivation_reason and participant.event.state in ['OPEN', 'RUNNING']:
                    participant.is_active = True
                    participant.activated_at = participant.activated_at or timezone.now()
                    from apps.audit.services import record
                    from apps.notifications.models import Notification
                    record(request.user, 'profile.activated', participant, participant.event, automatic=True)
                    Notification.objects.create(participant=participant, event=participant.event, title='Seu perfil foi ativado', body='Consulte o estado do evento para começar a descobrir participantes.')
            participant.registration_status = 'ACTIVE' if participant.is_active else 'INACTIVE' if participant.deactivation_reason else 'PENDING'
            participant.onboarding_completed_at = participant.onboarding_completed_at or timezone.now()
            participant.save()
            audit(request.user, "profile.updated" if participant.is_active else 'profile.pending', profile)
        return Response(bootstrap(participant))


class FiltersView(APIView):
    def put(self, request):
        serializer = FilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            participant = current(request)
            ensure_writable(participant)
            EventParticipant.objects.select_for_update().get(pk=participant.pk)
            preference = participant.preference
            preference.filters = {**serializer.validated_data, "favorites": preference.filters.get("favorites", [])}
            preference.save()
            audit(request.user, "filters.updated", preference)
        return Response(bootstrap(participant))


class ParticipantsView(APIView):
    def get(self, request):
        participant = current(request, active=True)
        ensure_social(participant)
        queryset = visible_participants(participant)
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(profile__first_name__icontains=search)
        return Response([person_payload(p) for p in queryset])


class ParticipantView(APIView):
    def get(self, request, peer_id):
        participant = current(request, active=True)
        peer = target_for(participant, peer_id)
        from apps.matches.models import Match
        from django.db.models import Q
        matched = Match.objects.filter(Q(participant=participant, partner=peer) | Q(partner=participant, participant=peer), is_active=True).exists()
        result = person_payload(peer)
        result["photos"] = [photo_url(p) for p in ordered_photos(peer) if p.visibility == "PRE_MATCH" or matched]
        outfit = getattr(peer, "outfit_photo", None)
        result["photoEvidence"] = [{'id':str(p.pk),'url':photo_url(p)} for p in ordered_photos(peer) if p.visibility=='PRE_MATCH' or matched]
        result["outfit"] = f'/api/outfits/{peer.pk}/content/?v={outfit.updated_at.timestamp()}' if matched and outfit else None
        return Response(result)


class DiscoveryView(APIView):
    def get(self, request):
        participant = current(request,active=True)
        ensure_social(participant)
        return Response(bootstrap(participant)['discovery'])


class InteractionView(APIView):
    def post(self, request, peer_id):
        serializer = DecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            participant = current(request, active=True)
            ensure_social(participant)
            target = target_for(participant, peer_id)
            list(EventParticipant.objects.select_for_update().filter(pk__in=[participant.pk, target.pk]).order_by("id"))
            target = target_for(participant, peer_id)
            matched = record_decision(participant, target, serializer.validated_data["decision"])
        return Response({"match": matched, "data": bootstrap(participant)})


class FavoriteView(APIView):
    def post(self, request, peer_id):
        with transaction.atomic():
            participant = current(request, active=True)
            target_for(participant, peer_id)
            ensure_writable(participant)
            match = match_for(participant,peer_id)
            if not match.is_active: raise PermissionDenied('Favoritar está disponível somente após match ativo.')
            EventParticipant.objects.select_for_update().get(pk=participant.pk)
            preference = participant.preference
            favorites = preference.filters.get("favorites", [])
            key = str(peer_id)
            preference.filters["favorites"] = [value for value in favorites if value != key] if key in favorites else [*favorites, key]
            preference.save()
        return Response({"saved": preference.filters["favorites"]})


class ConversationsView(APIView):
    def get(self, request):
        data = bootstrap(current(request))
        return Response({"chats": data["chats"], "chatStates": data["chatStates"]})


class MessagesView(APIView):
    @transaction.atomic
    def get(self, request, peer_id):
        participant = current(request)
        match = match_for(participant, peer_id)
        match.conversation.messages.exclude(sender=participant).filter(read_at__isnull=True).update(read_at=timezone.now())
        return Response(bootstrap(participant)["chats"].get(str(peer_id), []))

    def post(self, request, peer_id):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            participant = current(request)
            ensure_writable(participant)
            if participant.event.state not in ['RUNNING','PAUSED']:
                raise PermissionDenied('O evento ainda não começou.')
            match = match_for(participant, peer_id)
            from apps.matches.models import Match
            match = Match.objects.select_for_update().get(pk=match.pk)
            peer = match.partner if match.participant_id == participant.pk else match.participant
            if not match.is_active or blocked(participant, peer):
                raise PermissionDenied("Esta conversa está em modo somente leitura.")
            if peer.social_deleted_at or not peer.user.is_active or peer.active_ban:
                raise PermissionDenied('Esta conversa está disponível somente para consulta.')
            message = Message.objects.create(conversation=match.conversation, sender=participant, body=serializer.validated_data["text"])
            audit(request.user, "message.sent", message)
            from apps.notifications.services import notify
            notify(peer, 'message', f'Nova mensagem de {participant.profile.first_name}',
                   message.body, key=f'message:{message.pk}',
                   action_path=f'#mensagens?participant={participant.pk}')
        return Response(bootstrap(participant), status=201)


class EndMatchView(APIView):
    def post(self, request, peer_id):
        with transaction.atomic():
            participant = current(request, active=True)
            ensure_writable(participant)
            match = match_for(participant, peer_id)
            from apps.matches.models import Match
            match = Match.objects.select_for_update().get(pk=match.pk)
            if match.is_active:
                match.is_active = False
                match.ended_at = timezone.now()
                match.ended_by = request.user
                match.save()
                audit(request.user, "match.ended", match)
        return Response(bootstrap(participant))


def normalize_photos(participant):
    photos = ordered_photos(participant)
    for index, photo in enumerate(photos):
        photo.position = index
        if not participant.activated_at:
            photo.is_primary = index == 0
            photo.visibility = "PRE_MATCH" if index < 3 else "POST_MATCH"
        photo.save()
    if len(photos) < 3:
        participant.is_active = False
        participant.save(update_fields=["is_active", "updated_at"])
    return [photo_url(p) for p in photos]


class PhotosView(APIView):
    @transaction.atomic
    def put(self, request):
        serializer = PhotoDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = current(request)
        ensure_writable(participant)
        EventParticipant.objects.select_for_update().get(pk=participant.pk)
        photos = ordered_photos(participant)
        selected = next((photo for photo in photos if photo_url(photo) == serializer.validated_data['url']), None)
        if selected is None:
            raise Http404
        if selected.visibility != 'PRE_MATCH':
            raise ValidationError('Selecione uma das três fotos públicas como miniatura.')
        ordered = [selected] + [photo for photo in photos if photo.pk != selected.pk]
        for position, photo in enumerate(ordered):
            photo.position = position
            photo.is_primary = photo.pk == selected.pk
            photo.save(update_fields=['position', 'is_primary', 'updated_at'])
        audit(request.user, 'photo.thumbnail_selected', selected)
        return Response(bootstrap(participant))

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None or upload.size > 10 * 1024 * 1024:
            raise ValidationError("Envie uma imagem de até 10 MB.")
        try:
            image = Image.open(upload)
            if image.format not in {"JPEG", "PNG", "WEBP"} or image.width * image.height > 25_000_000:
                raise ValidationError("Formato ou dimensões de imagem inválidos.")
            extension = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}[image.format]
            image.verify()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
            raise ValidationError("O arquivo não é uma imagem válida.")
        upload.seek(0)
        key = None
        try:
            with transaction.atomic():
                participant = current(request)
                ensure_writable(participant)
                EventParticipant.objects.select_for_update().get(pk=participant.pk)
                if participant.photos.filter(removed_at__isnull=True).count() >= 10:
                    raise ValidationError("Limite de 10 fotos por perfil.")
                key = default_storage.save(f"participants/{participant.pk}/{uuid.uuid4()}{extension}", upload)
                replacement=participant.deactivation_reason=='PHOTO_REVIEW' and participant.photos.filter(visibility='PRE_MATCH',removed_at__isnull=True).count()<3
                photo = ParticipantPhoto.objects.create(participant=participant, storage_key=key, position=participant.photos.filter(removed_at__isnull=True).count(),visibility='PRE_MATCH' if replacement or not participant.activated_at else 'POST_MATCH',is_primary=replacement and not participant.photos.filter(removed_at__isnull=True,is_primary=True).exists())
                photos = normalize_photos(participant)
                audit(request.user, "photo.uploaded", photo)
        except Exception:
            if key:
                default_storage.delete(key)
            raise
        return Response({"photos": photos, "active": participant.is_active}, status=201)

    def delete(self, request):
        serializer = PhotoDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            participant = current(request)
            ensure_writable(participant)
            EventParticipant.objects.select_for_update().get(pk=participant.pk)
            photo = next((p for p in participant.photos.all() if photo_url(p) == serializer.validated_data["url"]), None)
            if photo is None:
                raise Http404
            if photo.removed_at:
                raise Http404
            if participant.activated_at and photo.visibility == 'PRE_MATCH':
                raise PermissionDenied('Esta foto faz parte do perfil aprovado para este evento e não pode ser alterada diretamente.')
            key = photo.storage_key
            audit(request.user, "photo.deleted", photo)
            photo.removed_at = timezone.now()
            photo.save(update_fields=['removed_at','updated_at'])
            photos = normalize_photos(participant)
        return Response({"photos": photos, "active": participant.is_active})


class PhotoContentView(APIView):
    def get(self, request, photo_id):
        participant = current(request)
        photo = get_object_or_404(ParticipantPhoto, pk=photo_id,removed_at__isnull=True)
        if photo.participant_id != participant.pk:
            current(request, active=True)
            peer = target_for(participant, photo.participant_id)
            if photo.visibility == "POST_MATCH":
                match = match_for(participant, peer.pk)
                if not match.is_active:
                    raise PermissionDenied("Foto disponível somente após match ativo.")
        if photo.storage_key.startswith("/images/") or not default_storage.exists(photo.storage_key):
            raise Http404
        response = FileResponse(default_storage.open(photo.storage_key, "rb"))
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
