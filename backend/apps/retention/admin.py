from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.DataRetentionRecord, BaseAdmin)

admin.site.register(models.LegalHold, BaseAdmin)

admin.site.register(models.PrivacyRequest, BaseAdmin)
