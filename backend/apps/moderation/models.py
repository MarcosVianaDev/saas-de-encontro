from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class ModerationCase(BaseModel):
    report = models.ForeignKey("reports.Report", on_delete=models.PROTECT, related_name="moderation_cases")
    assigned_to = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    notes = models.TextField(blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)


class ModerationAction(BaseModel):
    case = models.ForeignKey("moderation.ModerationCase", on_delete=models.PROTECT, related_name="actions")
    actor = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="+")
    description = models.TextField()


class ModerationNote(BaseModel):
    case = models.ForeignKey("moderation.ModerationCase", on_delete=models.PROTECT, related_name="case_notes")
    author = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="+")
    body = models.TextField()


class UserSuspension(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="suspensions")
    reason = models.TextField()
    ends_at = models.DateTimeField(null=True, blank=True)


class EventBan(BaseModel):
    participant = models.OneToOneField("participants.EventParticipant", on_delete=models.PROTECT, related_name="ban")
    reason = models.TextField()


class RoomBan(BaseModel):
    room = models.ForeignKey("rooms.Room", on_delete=models.PROTECT, related_name="bans")
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="room_bans")
    reason = models.TextField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=('room', 'participant'), name="moderation_roomban_unique")]
