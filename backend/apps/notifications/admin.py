from django.contrib import admin
from common.admin import BaseAdmin
from . import models

admin.site.register(models.Notification, BaseAdmin)
for model in [models.EventAnnouncement,models.SupportThread,models.SupportMessage]:
    admin.site.register(model,BaseAdmin)
