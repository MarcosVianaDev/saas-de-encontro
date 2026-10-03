from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.ModerationCase, BaseAdmin)

admin.site.register(models.ModerationAction, BaseAdmin)

admin.site.register(models.ModerationNote, BaseAdmin)

admin.site.register(models.UserSuspension, BaseAdmin)

admin.site.register(models.EventBan, BaseAdmin)

admin.site.register(models.RoomBan, BaseAdmin)
