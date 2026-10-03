from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from common.models import BaseModel


class AuditLog(BaseModel):
    actor = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="+", null=True, blank=True)
    action = models.CharField(max_length=200)
    object_label = models.CharField(max_length=200)
    object_id = models.UUIDField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            from django.core.exceptions import ValidationError
            raise ValidationError("Registros de auditoria não podem ser alterados.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError("Registros de auditoria não podem ser excluídos.")
