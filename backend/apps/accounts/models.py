from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel

import uuid
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class UserProfile(BaseModel):
    user = models.OneToOneField("accounts.User", on_delete=models.PROTECT, related_name="profile")
    bio = models.TextField(blank=True)
    preferences = models.JSONField(default=dict, blank=True)
