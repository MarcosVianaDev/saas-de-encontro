from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.Interaction, BaseAdmin)

admin.site.register(models.InteractionHistory, BaseAdmin)
