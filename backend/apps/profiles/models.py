from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class ParticipantProfile(BaseModel):
    participant = models.OneToOneField("participants.EventParticipant", on_delete=models.PROTECT, related_name="profile")
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    birth_month = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    job = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, default="São Paulo, SP")
    interests = models.JSONField(default=list, blank=True)
    is_online = models.BooleanField(default=False)


class ParticipantPhoto(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="photos")
    storage_key = models.CharField(max_length=1024)
    is_primary = models.BooleanField(default=False)
    position = models.PositiveSmallIntegerField(default=0)
    visibility = models.CharField(max_length=20, choices=[("PRE_MATCH", "Antes do match"), ("POST_MATCH", "Após o match")], default="PRE_MATCH")


class EventOutfitPhoto(BaseModel):
    participant = models.OneToOneField("participants.EventParticipant", on_delete=models.PROTECT, related_name="outfit_photo")
    storage_key = models.CharField(max_length=1024)


class ProfileField(BaseModel):
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="profile_fields", null=True, blank=True)
    name = models.CharField(max_length=200)
    is_required = models.BooleanField(default=False)


class ProfileFieldOption(BaseModel):
    field = models.ForeignKey("profiles.ProfileField", on_delete=models.PROTECT, related_name="options")
    name = models.CharField(max_length=200)


class ParticipantFieldValue(BaseModel):
    participant = models.ForeignKey("participants.EventParticipant", on_delete=models.PROTECT, related_name="field_values")
    field = models.ForeignKey("profiles.ProfileField", on_delete=models.PROTECT, related_name="values")
    value = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('participant', 'field'), name="profiles_participantfieldvalue_unique")]


class ParticipantPreference(BaseModel):
    participant = models.OneToOneField("participants.EventParticipant", on_delete=models.PROTECT, related_name="preference")
    filters = models.JSONField(default=dict, blank=True)
