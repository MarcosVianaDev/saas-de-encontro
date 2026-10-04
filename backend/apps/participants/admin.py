from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.EventParticipant, BaseAdmin)
for model in [models.LocationReading,models.LocationAnomaly,models.LocationException]:
    admin.site.register(model,BaseAdmin)
