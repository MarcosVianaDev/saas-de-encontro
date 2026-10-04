from django.db import transaction
from rest_framework.exceptions import APIException
from .models import AuditLog


class AuditUnavailable(APIException):
    status_code = 503
    default_detail = 'Não foi possível concluir a operação com segurança. Tente novamente.'


def record(actor, action, obj, event=None, **details):
    """Mandatory writes run inside the caller's transaction; audit failure aborts it."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError('A operação auditável deve estar em uma transação.')
    try:
        with transaction.atomic():
            return AuditLog.objects.create(actor=actor, action=action, object_label=obj._meta.label,
                object_id=obj.pk, details={**({'event': str(event.pk)} if event else {}), **details})
    except Exception as error:
        raise AuditUnavailable() from error
