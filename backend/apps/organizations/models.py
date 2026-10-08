from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Organization(BaseModel):
    contact_name = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    onboarding_draft = models.JSONField(default=dict, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)


class OrganizationMember(BaseModel):
    role = models.CharField(max_length=20, choices=[('ADMIN', 'Responsável pelo evento'), ('MODERATOR', 'Moderador'), ('OPERATOR', 'Operador')], default='ADMIN')
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="members")
    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="organization_memberships")

    class Meta:
        constraints = [models.UniqueConstraint(fields=('organization', 'user'), name="organizations_organizationmember_unique")]
