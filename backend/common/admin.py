from django.contrib import admin
from django.db import transaction


class BaseAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at")
    readonly_fields = ("id", "created_at", "updated_at")
    list_per_page = 50
    date_hierarchy = "created_at"

    def save_model(self, request, obj, form, change):
        from apps.audit.services import record
        with transaction.atomic():
            super().save_model(request, obj, form, change)
            if obj._meta.label_lower != 'audit.auditlog':
                record(request.user, 'admin.changed' if change else 'admin.created', obj,
                    changed_fields=form.changed_data)

    def delete_model(self, request, obj):
        from apps.audit.services import record
        with transaction.atomic():
            record(request.user, 'admin.deleted', obj)
            super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        from apps.audit.services import record
        with transaction.atomic():
            for obj in queryset:
                record(request.user, 'admin.deleted', obj)
            super().delete_queryset(request, queryset)

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self.list_display = tuple(
            field.name for field in model._meta.fields
            if field.name not in {"updated_at", "password"} and field.get_internal_type() not in {"TextField", "JSONField"}
        )[:7]
        self.search_fields = tuple(
            field.name for field in model._meta.fields
            if field.get_internal_type() in {"CharField", "EmailField"}
        )
        self.autocomplete_fields = tuple(
            field.name for field in model._meta.fields
            if field.is_relation and (field.many_to_one or field.one_to_one)
        )
        # All related admin classes need a searchable field, including UUID models.
        self.search_fields += ("=id",)
