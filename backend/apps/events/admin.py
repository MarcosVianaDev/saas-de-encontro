from django.contrib import admin
from common.admin import BaseAdmin
from . import models

@admin.register(models.Event)
class EventAdmin(BaseAdmin):
    readonly_fields = BaseAdmin.readonly_fields + ('state', 'opened_at', 'opening_origin', 'closed_at', 'archived_at')

    def save_model(self,request,obj,form,change):
        if not change:return super().save_model(request,obj,form,change)
        from .services import configure
        configure(obj,request.user,{key:getattr(obj,obj._meta.get_field(key).attname) for key in form.changed_data},confirmed=True)

admin.site.register(models.EventAdministrator, BaseAdmin)
