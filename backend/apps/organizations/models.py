from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class Organization(BaseModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)


class OrganizationMember(BaseModel):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT, related_name="members")
    user = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="organization_memberships")

    class Meta:
        constraints = [models.UniqueConstraint(fields=('organization', 'user'), name="organizations_organizationmember_unique")]
