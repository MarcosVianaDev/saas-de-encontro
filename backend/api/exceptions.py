from django.core.exceptions import ValidationError
from rest_framework.views import exception_handler as default_handler
from rest_framework.views import set_rollback
from rest_framework.response import Response
import logging


def exception_handler(error, context):
    if isinstance(error, ValidationError):
        set_rollback()
        errors = error.message_dict if hasattr(error, 'error_dict') else {'non_field_errors': error.messages}
        return Response(errors, status=400)
    response=default_handler(error,context)
    if response is not None:return response
    logging.getLogger(__name__).exception('Falha interna na API',exc_info=error)
    return Response({'detail':'Não foi possível concluir a operação. Tente novamente.'},status=500)
