from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.Organization, BaseAdmin)

admin.site.register(models.OrganizationMember, BaseAdmin)
