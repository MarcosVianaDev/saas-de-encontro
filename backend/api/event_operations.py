import secrets
from datetime import timedelta
from django.db import transaction
from django.core.exceptions import ValidationError as ModelValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.events.models import Event
from apps.events.services import transition, is_manager, TRANSITIONS
from apps.events.services import configure
from apps.audit.services import record


def managed_event(request):
    event = get_object_or_404(Event, pk=request.session.get('event_id'))
    if not is_manager(request.user, event):
        raise PermissionDenied('Seu papel não permite gerenciar o evento.')
    return event


def event_data(event, actor=None):
    actions=[state for state in TRANSITIONS[event.state] if state!='ARCHIVED']
    now=timezone.now()
    if 'OPEN' in actions and (not event.starts_at or now<event.starts_at-timedelta(hours=2)):actions.remove('OPEN')
    if 'RUNNING' in actions and event.state=='OPEN' and (not event.starts_at or now<event.starts_at+(timedelta(minutes=10) if event.opening_origin=='automatic' else timedelta())):actions.remove('RUNNING')
    if 'SCHEDULED' in actions and (not event.starts_at or not event.ends_at):actions.remove('SCHEDULED')
    if 'SCHEDULED' in actions and event.requested_by_id and not (actor and actor.is_superuser):
        actions.remove('SCHEDULED')
    return {'state': event.state, 'status': event.get_state_display(),
        'pendingApproval': bool(event.requested_by_id and event.state == 'DRAFT'),
        'canEditRequestedDraft': bool(event.requested_by_id and event.state == 'DRAFT'),
        'timeline': [{'state': state, 'label': label} for state, label in Event.State.choices],
        'actions': actions,
        'configuration': {field: getattr(event, field) for field in ['name', 'description', 'starts_at', 'ends_at',
            'mode', 'latitude', 'longitude', 'radius_m', 'tolerance_m', 'location_interval_minutes', 'settings','pass_payment_instructions']}}


class EventTransitionView(APIView):
    def get(self, request):
        event = managed_event(request)
        left, right = secrets.randbelow(9) + 1, secrets.randbelow(9) + 1
        request.session['closing_challenge'] = {'answer': str(left + right), 'event': str(event.pk),
            'expires': timezone.now().timestamp() + 300}
        return Response({**event_data(event, request.user), 'challenge': f'Quanto é {left} + {right}?'})

    def post(self, request):
        event = managed_event(request)
        state = request.data.get('state')
        if state in ['PAUSED', 'CLOSED'] and request.data.get('confirmed') is not True:
            raise ValidationError('Confirme explicitamente esta alteração.')
        if state == 'CLOSED' and event.ends_at and timezone.now() < event.ends_at:
            challenge = request.session.pop('closing_challenge', {})
            if challenge.get('event') != str(event.pk) or challenge.get('expires', 0) < timezone.now().timestamp() or challenge.get('answer') != str(request.data.get('captcha', '')):
                raise ValidationError('Verificação inválida ou expirada. Solicite uma nova verificação.')
        event = transition(event, state, actor=request.user, reason=str(request.data.get('reason', '')).strip())
        return Response(event_data(event, request.user))


class EventConfigurationView(APIView):
    def get(self, request):
        return Response(event_data(managed_event(request), request.user))

    @transaction.atomic
    def put(self, request):
        event=configure(managed_event(request),request.user,{key:value for key,value in request.data.items() if key!='confirmed'},request.data.get('confirmed') is True)
        return Response(event_data(event, request.user))
