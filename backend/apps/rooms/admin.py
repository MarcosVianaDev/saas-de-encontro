from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.Room, BaseAdmin)

admin.site.register(models.RoomConfiguration, BaseAdmin)

admin.site.register(models.RoomAdministrator, BaseAdmin)

admin.site.register(models.RoomParticipant, BaseAdmin)
