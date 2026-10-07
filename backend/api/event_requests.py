from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from apps.audit.services import record
from apps.events.models import Event, EventAdministrator
from apps.notifications.models import Notification
from .event_operations import managed_event


class EventDetailsSerializer(serializers.Serializer):
    event = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length=4000, required=False, allow_blank=True, default='')
    mode = serializers.ChoiceField(choices=['ONLINE', 'PHYSICAL', 'HYBRID'], default='PHYSICAL')
    starts = serializers.DateTimeField()
    ends = serializers.DateTimeField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True, min_value=-90, max_value=90)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True, min_value=-180, max_value=180)
    radius_m = serializers.IntegerField(min_value=1, default=100)
    tolerance_m = serializers.IntegerField(min_value=0, default=1000)
    location_interval_minutes = serializers.IntegerField(min_value=1, default=15)
    auto_activate_participants = serializers.BooleanField(default=False)

    def validate(self, data):
        if data['ends'] <= data['starts']:
            raise serializers.ValidationError('O término deve ser posterior ao início.')
        if data['mode'] != 'ONLINE' and (data.get('latitude') is None or data.get('longitude') is None):
            raise serializers.ValidationError('Informe latitude e longitude do evento presencial.')
        if data['auto_activate_participants'] and data['mode'] != 'ONLINE':
            raise serializers.ValidationError('A ativação automática está disponível somente para eventos online.')
        return data


def event_details(values):
    return {
        'name': values['event'], 'description': values['description'], 'mode': values['mode'],
        'starts_at': values['starts'], 'ends_at': values['ends'],
        'latitude': values.get('latitude') if values['mode'] != 'ONLINE' else None,
        'longitude': values.get('longitude') if values['mode'] != 'ONLINE' else None,
        'radius_m': values['radius_m'], 'tolerance_m': values['tolerance_m'],
        'location_interval_minutes': values['location_interval_minutes'],
        'settings': {'auto_activate_participants': values['auto_activate_participants']},
    }


class EventRequestView(APIView):
    @transaction.atomic
    def post(self, request):
        source = managed_event(request)
        if not source.organization.is_active:
            raise ValidationError('A organização precisa estar ativa para solicitar um evento.')
        serializer = EventDetailsSerializer(data=request.data)
        if set(request.data) - set(serializer.fields):
            raise ValidationError('A solicitação aceita apenas os dados do evento.')
        serializer.is_valid(raise_exception=True)
        event = Event(organization=source.organization, responsible=request.user,
            requested_by=request.user, **event_details(serializer.validated_data))
        try:
            event.full_clean()
        except ModelValidationError as error:
            raise ValidationError(error.message_dict)
        event.save()
        EventAdministrator.objects.create(event=event, user=request.user, role='ADMIN')
        record(request.user, 'event.requested', event, event, source_event=str(source.pk))
        Notification.objects.bulk_create([
            Notification(recipient=user, event=event, title='Novo evento solicitado',
                body=f'{event.name} foi salvo como rascunho e aguarda aprovação.')
            for user in get_user_model().objects.filter(is_superuser=True, is_active=True)
        ])
        return Response({'id': str(event.pk), 'state': event.state, 'pendingApproval': True}, status=201)
