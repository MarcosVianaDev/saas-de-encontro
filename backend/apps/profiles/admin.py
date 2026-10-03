from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.ParticipantProfile, BaseAdmin)

admin.site.register(models.ParticipantPhoto, BaseAdmin)

admin.site.register(models.EventOutfitPhoto, BaseAdmin)

admin.site.register(models.ProfileField, BaseAdmin)

admin.site.register(models.ProfileFieldOption, BaseAdmin)

admin.site.register(models.ParticipantFieldValue, BaseAdmin)

admin.site.register(models.ParticipantPreference, BaseAdmin)
