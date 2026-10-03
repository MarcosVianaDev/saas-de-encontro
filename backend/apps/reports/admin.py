from django.contrib import admin
from common.admin import BaseAdmin
from . import models

@admin.register(models.Block)
class BlockAdmin(BaseAdmin):
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(models.Report, BaseAdmin)

admin.site.register(models.ReportEvidence, BaseAdmin)
