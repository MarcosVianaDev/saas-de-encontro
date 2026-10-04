from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.audit.models import AuditLog
from apps.discovery.models import ProfileDiscovery
from apps.interactions.models import Interaction, InteractionHistory
from apps.matches.models import Match
from apps.messaging.models import Conversation
from apps.moderation.models import EventBan, UserSuspension
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ParticipantPreference
from apps.reports.models import Block


DEFAULT_FILTERS = {"min": 18, "max": 35, "gender": "Todos", "interests": [], "purpose": "Networking"}


def audit(actor, action, obj):
    AuditLog.objects.create(actor=actor, action=action, object_label=obj._meta.label, object_id=obj.pk)


def current(request, active=False):
    suspended = UserSuspension.objects.filter(user=request.user).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now())).exists()
    if suspended:
        raise PermissionDenied("Sua conta está suspensa.")
    participant = get_object_or_404(EventParticipant.objects.select_related("event", "user"),
        user=request.user, event_id=request.session.get("event_id"))
    if EventBan.objects.filter(participant=participant).exists():
        raise PermissionDenied("Participação indisponível neste evento.")
    if active and not participant.is_active:
        raise PermissionDenied("Complete e ative seu perfil antes de continuar.")
    return participant


def blocked(first, second):
    return Block.objects.filter(Q(participant=first, target=second) | Q(participant=second, target=first)).exists()


def visible_participants(participant):
    blocked_ids = list(Block.objects.filter(participant=participant).values_list("target_id", flat=True))
    blocked_ids += list(Block.objects.filter(target=participant).values_list("participant_id", flat=True))
    suspended = UserSuspension.objects.filter(Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now())).values_list("user_id", flat=True)
    return EventParticipant.objects.filter(event=participant.event, is_active=True, user__is_active=True, ban__isnull=True).exclude(pk=participant.pk).exclude(pk__in=blocked_ids).exclude(user_id__in=suspended).select_related("profile").prefetch_related("photos").order_by("created_at", "id")


def target_for(participant, target_id):
    return get_object_or_404(visible_participants(participant), pk=target_id)


def age(profile):
    today = timezone.localdate()
    if not profile.birth_year or not profile.birth_month:
        return None
    return today.year - profile.birth_year - (today.month < profile.birth_month)


def photo_url(photo):
    # Seed images are public, fictitious assets. Uploaded images require an authenticated API request.
    return photo.storage_key if photo.storage_key.startswith("/images/") else f"/api/photos/{photo.id}/content/"


def ordered_photos(participant):
    return sorted(participant.photos.all(), key=lambda item: (item.position, item.created_at))


def person_payload(person):
    profile = getattr(person, "profile", None)
    images = ordered_photos(person)
    primary = next((image for image in images if image.is_primary), None)
    return {"id": str(person.id), "name": profile.first_name if profile else person.user.first_name,
        "age": age(profile) if profile else None, "gender": profile.gender if profile else "",
        "job": profile.job if profile else "", "city": profile.city if profile else "",
        "image": photo_url(primary) if primary else "/images/profile-placeholder.svg",
        "interests": profile.interests if profile else [], "online": profile.is_online if profile else False,
        "mutual": False, "bio": profile.bio if profile else ""}


def match_for(participant, peer_id):
    return get_object_or_404(Match.objects.select_related("participant", "partner"),
        Q(participant=participant, partner_id=peer_id) | Q(partner=participant, participant_id=peer_id))


def chat_payload(participant):
    chats, states = {}, {}
    matches = Match.objects.filter(Q(participant=participant) | Q(partner=participant)).select_related("conversation", "participant", "partner")
    for match in matches:
        peer = match.partner if match.participant_id == participant.pk else match.participant
        conversation = getattr(match, "conversation", None)
        if conversation is None:
            continue
        key = str(peer.pk)
        chats[key] = [{"text": message.body, "mine": message.sender_id == participant.pk,
            "time": timezone.localtime(message.created_at).strftime("%H:%M")} for message in conversation.messages.order_by("created_at", "id")]
        inaccessible = not visible_participants(participant).filter(pk=peer.pk).exists()
        states[key] = {"active": match.is_active and not inaccessible, "blocked": inaccessible}
    return chats, states


def discovery(participant, filters):
    if not participant.is_active:
        return []
    decided = Interaction.objects.filter(participant=participant).values_list("target_id", flat=True)
    candidates = []
    for target in visible_participants(participant).exclude(id__in=decided):
        data = person_payload(target)
        if data["age"] is None or not filters["min"] <= data["age"] <= filters["max"]:
            continue
        if filters["gender"] != "Todos" and data["gender"] != filters["gender"]:
            continue
        if filters["interests"] and not set(filters["interests"]).intersection(data["interests"]):
            continue
        candidates.append(data)
    return candidates


def bootstrap(participant):
    profile, _ = ParticipantProfile.objects.get_or_create(participant=participant)
    preference, _ = ParticipantPreference.objects.get_or_create(participant=participant, defaults={"filters": DEFAULT_FILTERS})
    filters = {**DEFAULT_FILTERS, **{key: value for key, value in preference.filters.items() if key in DEFAULT_FILTERS}}
    chats, states = chat_payload(participant) if participant.is_active else ({}, {})
    participants = [person_payload(p) for p in visible_participants(participant)] if participant.is_active else []
    # Keep ended/blocked conversations available without identifying a blocked peer.
    known = {data["id"] for data in participants}
    for peer_id, state in states.items():
        if peer_id not in known:
            peer = EventParticipant.objects.select_related("profile").get(id=peer_id)
            data = person_payload(peer)
            if state["blocked"]:
                data.update(name="Usuário bloqueado", image="/images/profile-placeholder.svg", job="", city="", gender="", bio="", interests=[], online=False, age=0)
            participants.append(data)
    return {"profile": {"first": profile.first_name, "last": profile.last_name, "month": str(profile.birth_month or 1),
            "year": str(profile.birth_year or ""), "gender": profile.gender or "Prefiro não informar", "bio": profile.bio},
        "photos": [photo_url(photo) for photo in ordered_photos(participant)],
        "active": participant.is_active, "filters": filters, "people": participants,
        "discovery": discovery(participant, filters), "chats": chats, "chatStates": states,
        "seen": [str(pk) for pk in Interaction.objects.filter(participant=participant).values_list("target_id", flat=True)],
        "liked": [str(pk) for pk in Interaction.objects.filter(participant=participant, decision="LIKE").values_list("target_id", flat=True)],
        "saved": preference.filters.get("favorites", []),
        "event": {"id": str(participant.event_id), "name": participant.event.name}}


def record_decision(participant, target, decision):
    ProfileDiscovery.objects.get_or_create(participant=participant, candidate=target)
    interaction, created = Interaction.objects.get_or_create(participant=participant, target=target, defaults={"decision": decision})
    if created or interaction.decision != decision:
        interaction.decision = decision
        interaction.save()
        InteractionHistory.objects.create(interaction=interaction, decision=decision)
        audit(participant.user, "interaction." + decision.lower(), interaction)
    matched = None
    if decision == "LIKE" and Interaction.objects.filter(participant=target, target=participant, decision="LIKE").exists():
        first, second = sorted([participant, target], key=lambda p: p.pk.int)
        match, created = Match.objects.get_or_create(participant=first, partner=second)
        if match.is_active:
            Conversation.objects.get_or_create(match=match)
            matched = person_payload(target)
            if created:
                audit(participant.user, "match.created", match)
    return matched
