from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at")
    readonly_fields = ("id", "created_at", "updated_at")
    list_per_page = 50
    date_hierarchy = "created_at"

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
