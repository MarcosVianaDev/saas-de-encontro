from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.PassType, BaseAdmin)

admin.site.register(models.EventPassOffer, BaseAdmin)

admin.site.register(models.ParticipantPass, BaseAdmin)

admin.site.register(models.PassUsage, BaseAdmin)

admin.site.register(models.PassActivation, BaseAdmin)


@admin.register(models.InitialGiftSweep)
class InitialGiftSweepAdmin(admin.ModelAdmin):
    list_display = ('id', 'token', 'cursor', 'expires_at')
    readonly_fields = list_display

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
