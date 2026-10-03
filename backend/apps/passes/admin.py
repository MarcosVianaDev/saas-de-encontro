from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.PassType, BaseAdmin)

admin.site.register(models.EventPassOffer, BaseAdmin)

admin.site.register(models.ParticipantPass, BaseAdmin)

admin.site.register(models.PassUsage, BaseAdmin)

admin.site.register(models.PassActivation, BaseAdmin)
