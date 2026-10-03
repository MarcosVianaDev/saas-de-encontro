import uuid
from django.core.exceptions import ValidationError
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return str(getattr(self, "name", None) or getattr(self, "title", None) or self.pk)

    def clean(self):
        super().clean()
        # Validate event context in admin forms without hiding related objects.
        event_ids = set()
        participants = []
        for field in self._meta.fields:
            if not field.is_relation or not getattr(self, field.attname, None):
                continue
            related = getattr(self, field.name)
            if field.related_model._meta.label_lower == "events.event":
                event_ids.add(related.pk)
            elif hasattr(related, "event_id"):
                event_ids.add(related.event_id)
            if field.related_model._meta.label_lower == "participants.eventparticipant":
                participants.append(related.pk)
        if len(event_ids) > 1:
            raise ValidationError("Os vínculos devem pertencer ao mesmo evento.")
        if len(participants) != len(set(participants)):
            raise ValidationError("Selecione participantes distintos.")
