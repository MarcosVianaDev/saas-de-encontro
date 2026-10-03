from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Room(BaseModel):
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="rooms")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)


class RoomConfiguration(BaseModel):
    room = models.OneToOneField("rooms.Room", on_delete=models.PROTECT, related_name="configuration")
    settings = models.JSONField(default=dict, blank=True)


class RoomAdministrator(BaseModel):
    room = models.ForeignKey("rooms.Room", on_delete=models.PROTECT, related_name="administrators")
    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="+")

    class Meta:
        constraints = [models.UniqueConstraint(fields=('room', 'user'), name="rooms_roomadministrator_unique")]


class RoomParticipant(BaseModel):
    room = models.ForeignKey("rooms.Room", on_delete=models.PROTECT, related_name="participants")
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="room_memberships")

    class Meta:
        constraints = [models.UniqueConstraint(fields=('room', 'participant'), name="rooms_roomparticipant_unique")]
