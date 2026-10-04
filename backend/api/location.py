from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied,ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.participants.models import EventParticipant,LocationReading,LocationAnomaly
from apps.moderation.models import EventBan
from apps.participants.location import reading,failed,exception
from apps.events.services import is_manager
from apps.events.permissions import require
from apps.audit.services import record
from .services import current,bootstrap,ensure_writable
from .event_admin import access


class LocationView(APIView):
    @transaction.atomic
    def post(self,request):
        p=current(request);ensure_writable(p)
        if p.event.mode=='ONLINE':return Response(bootstrap(p))
        action=request.data.get('action','reading')
        if action=='deny':
            p.location_consent=False;p.presence='UNKNOWN';p.save()
            record(request.user,'location.revoked',p,p.event)
        elif action=='failed':p=failed(p,request.data.get('phase','periodic'))
        elif action=='reading':p=reading(p,request.data)
        else:raise ValidationError('Ação inválida.')
        return Response(bootstrap(p))


class LocationExceptionView(APIView):
    def post(self,request,participant_id):
        member=access(request);require(member,'location_exception')
        p=get_object_or_404(EventParticipant,pk=participant_id,event=member.event)
        ensure_writable(p)
        try:minutes=int(request.data.get('minutes',0))
        except (TypeError,ValueError):raise ValidationError('Duração inválida.')
        exception(p,request.user,minutes,str(request.data.get('reason','')))
        return Response({'ok':True})


class LocationHistoryView(APIView):
    @transaction.atomic
    def post(self,request,participant_id):
        member=access(request)
        if not is_manager(request.user,member.event):raise PermissionDenied('Somente a gestão responsável pode consultar o histórico individual.')
        if member.event.state not in ['PAUSED','CLOSED','ARCHIVED']:raise PermissionDenied('O histórico de localização não pode ser consultado enquanto o evento está aberto ou em andamento. Pause o evento para iniciar uma investigação que exija esse acesso.')
        reason=str(request.data.get('reason','')).strip()
        if not reason or len(reason)>4000:raise ValidationError('Informe o motivo da consulta (até 4.000 caracteres).')
        p=get_object_or_404(EventParticipant,pk=participant_id,event=member.event)
        record(request.user,'location.history_viewed',p,member.event,reason=reason)
        return Response([{'id':str(r.pk),'latitude':r.latitude,'longitude':r.longitude,'accuracy':r.accuracy_m,'distance':r.distance_m,'speed':r.speed_kmh,'anomalous':r.anomalous,'measured':r.measured_at,
            'anomaly':{'id':str(r.anomaly.pk),'criterion':r.anomaly.criterion,'resolution':r.anomaly.resolution,'reason':r.anomaly.reason} if hasattr(r,'anomaly') else None} for r in p.location_readings.select_related('anomaly').order_by('measured_at')])


class LocationDecisionView(APIView):
    @transaction.atomic
    def post(self,request,participant_id):
        member=access(request)
        if not is_manager(request.user,member.event):raise PermissionDenied('A decisão exige a gestão responsável pelo evento.')
        from apps.events.models import Event
        event=Event.objects.select_for_update().get(pk=member.event.pk)
        if event.state!='PAUSED':raise PermissionDenied('Pause o evento para registrar uma decisão operacional sobre localização.')
        p=get_object_or_404(EventParticipant.objects.select_for_update(),pk=participant_id,event=event)
        anomaly=get_object_or_404(LocationAnomaly.objects.select_for_update(),pk=request.data.get('anomaly'),participant=p)
        action=request.data.get('resolution');reason=str(request.data.get('reason','')).strip()
        if action not in ['DISCARDED','NO_RESTRICTION','EVENT_BAN','REVOKE_BAN'] or not reason or len(reason)>4000 or request.data.get('confirmed') is not True:raise ValidationError('Selecione o desfecho, informe o motivo e confirme a decisão.')
        if action=='EVENT_BAN':
            if p.active_ban:raise ValidationError('O participante já possui um banimento ativo. Revise a ocorrência original.')
            EventBan.objects.update_or_create(participant=p,defaults={'reason':reason,'location_anomaly':anomaly,'revoked_at':None,'revoked_by':None,'revocation_reason':''})
        elif action=='REVOKE_BAN':
            ban=get_object_or_404(EventBan,participant=p,location_anomaly=anomaly,revoked_at__isnull=True)
            ban.revoked_at=timezone.now();ban.revoked_by=request.user;ban.revocation_reason=reason;ban.save()
        anomaly.resolution='NO_RESTRICTION' if action=='REVOKE_BAN' else action
        anomaly.reason=reason;anomaly.resolved_by=request.user;anomaly.save()
        record(request.user,'location.decision',anomaly,event,resolution=action,reason=reason,participant=str(p.pk))
        return Response({'ok':True})
