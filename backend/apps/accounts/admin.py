from django.contrib import admin
from common.admin import BaseAdmin
from . import models

from django.contrib.auth.admin import UserAdmin


@admin.register(models.User)
class AccountAdmin(UserAdmin):
    readonly_fields = ("id",)
    fieldsets = UserAdmin.fieldsets + (("Identificação", {"fields": ("id",)}),)

admin.site.register(models.UserProfile, BaseAdmin)
