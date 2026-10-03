from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.Conversation, BaseAdmin)

admin.site.register(models.Message, BaseAdmin)
