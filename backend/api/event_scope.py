from uuid import UUID

from rest_framework.exceptions import ValidationError


def explicit_event_id(request):
    path_id = getattr(request, 'explicit_event_id', None)
    header_id = request.headers.get('X-Event-ID')
    try:
        path_id = UUID(str(path_id)) if path_id is not None else None
        header_id = UUID(header_id) if header_id is not None else None
    except (ValueError, TypeError, AttributeError):
        raise ValidationError('Identificador do evento inválido.')
    if path_id is not None and header_id is not None and path_id != header_id:
        raise ValidationError('O evento da URL difere do cabeçalho X-Event-ID.')
    return path_id or header_id


def event_id(request, *, required=True):
    if not required and hasattr(request, 'selected_context'):
        return request.selected_context.get('event')
    identifier = explicit_event_id(request)
    if identifier is None:
        if required:
            raise ValidationError('Informe o evento no cabeçalho X-Event-ID ou na URL.')
        # Session context is only a discovery/legacy participant default. Event
        # administration must always supply an explicit scope on every request.
        return request.session.get('event_id')
    return identifier


def navigation_context(request):
    if hasattr(request, 'selected_context'):
        return request.selected_context['navigation']
    context = request.headers.get('X-App-Context')
    if context is not None and context not in ['global', 'administration', 'participant', 'selection']:
        raise ValidationError('Contexto de acesso inválido.')
    return context or request.session.get('navigation')
