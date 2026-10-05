from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied,ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.passes.models import PassType,EventPassOffer,ParticipantPass,PassActivation
from apps.passes.services import revealed_ids,reveal,incoming,reveal_available
from apps.audit.services import record
from apps.events.permissions import require
from apps.participants.models import EventParticipant
from .services import current,person_payload,ensure_social
from .event_admin import access


def offer_payload(offer):
    return {'id':str(offer.pk),'name':offer.pass_type.name,'price':str(offer.price),'currency':offer.currency,
        'limit':offer.pass_type.reveal_limit,'durationMinutes':int(offer.pass_type.duration.total_seconds()/60) if offer.pass_type.duration else None}


class LikesReceivedView(APIView):
    def get(self,request):
        p=current(request,active=True);ensure_social(p)
        reveal_available(p)
        known=revealed_ids(p);likes=list(incoming(p))
        return Response({'count':len(likes),'hidden':sum(str(i.participant_id) not in known for i in likes),
            'instructions':p.event.pass_payment_instructions or 'Procure o atendimento do evento para ativar este passe.',
            'people':[person_payload(i.participant) for i in likes if str(i.participant_id) in known],
            'offers':[offer_payload(o) for o in p.event.pass_offers.select_related('pass_type')]})

    @transaction.atomic
    def post(self,request):
        p=current(request,active=True);ensure_social(p)
        usage,remaining=reveal(p,incoming(p))
        return Response({'person':person_payload(usage.revealed_participant),'remaining':remaining})


class AdminPassView(APIView):
    def get(self,request):
        member=access(request);require(member,'passes')
        return Response({'canEditOffers':member.role=='ADMIN' and member.event.state in ['DRAFT','SCHEDULED','OPEN'],'offers':[offer_payload(o) for o in member.event.pass_offers.select_related('pass_type')],
            'passes':[{'id':str(p.pk),'participant':str(p.participant_id),'name':p.offer_name or p.offer.pass_type.name,'amount':str(p.sale_amount),
                'created':p.created_at,'expires':p.expires_at,'revoked':p.revoked_at,'operator':p.granted_by.email if p.granted_by else 'Histórico',
                'origin':p.origin,'used':p.usages.count(),'limit':p.reveal_limit} for p in ParticipantPass.objects.filter(participant__event=member.event).select_related('offer__pass_type','granted_by')]})

    @transaction.atomic
    def post(self,request):
        member=access(request);require(member,'passes')
        action=request.data.get('action','grant')
        if member.event.state in ['CLOSED','ARCHIVED']:raise PermissionDenied('Passes em modo somente leitura após encerramento.')
        if action=='offer':
            if member.role!='ADMIN':raise PermissionDenied('Somente a gestão define as ofertas.')
            if member.event.state not in ['DRAFT','SCHEDULED','OPEN']:raise PermissionDenied('Tipos de passe bloqueados em andamento.')
            try:
                minutes=int(request.data.get('minutes',0));limit=int(request.data.get('limit',0));price=Decimal(str(request.data.get('price','0')))
                if minutes<0 or limit<0 or not price.is_finite() or price<0 or bool(minutes)==bool(limit):raise ValueError()
            except (ValueError,TypeError,ArithmeticError):raise ValidationError('Informe quantidade ou duração e preço válido.')
            name=str(request.data.get('name','')).strip()
            if not name or len(name)>200:raise ValidationError('Informe um nome de oferta válido.')
            try:duration=timedelta(minutes=minutes) if minutes else None
            except OverflowError:raise ValidationError('Duração inválida.')
            kind=PassType(name=name,duration=duration,reveal_limit=limit or None);kind.full_clean();kind.save()
            previous={}
            if request.data.get('id'):
                offer=get_object_or_404(EventPassOffer.objects.select_for_update(),pk=request.data['id'],event=member.event)
                previous=offer_payload(offer)
                offer.participant_passes.filter(offer_name='').update(offer_name=offer.pass_type.name)
                offer.pass_type=kind;offer.price=price;offer.full_clean();offer.save()
            else:
                offer=EventPassOffer(event=member.event,pass_type=kind,price=price);offer.full_clean();offer.save()
            record(request.user,'pass.offer',offer,member.event,previous=previous,values=offer_payload(offer))
        elif action=='grant':
            if member.role!='OPERATOR':raise PermissionDenied('A concessão é realizada por Operador com permissão específica.')
            p=get_object_or_404(EventParticipant.objects.select_for_update(),pk=request.data.get('participant'),event=member.event)
            offer=get_object_or_404(EventPassOffer,pk=request.data.get('offer'),event=member.event)
            origin=str(request.data.get('origin','')).strip()
            if not origin or len(origin)>100:raise ValidationError('Informe a origem da concessão (até 100 caracteres).')
            obj=ParticipantPass.objects.create(participant=p,offer=offer,offer_name=offer.pass_type.name,granted_by=request.user,origin=origin,
                reference=str(request.data.get('reference',''))[:500],sale_amount=offer.price,reveal_limit=offer.pass_type.reveal_limit,
                expires_at=timezone.now()+offer.pass_type.duration if offer.pass_type.duration else None)
            PassActivation.objects.create(participant_pass=obj,activated_by=request.user)
            record(request.user,'pass.granted',obj,member.event,amount=str(obj.sale_amount),origin=origin,participant=str(p.pk),offer=str(offer.pk))
            reveal_available(p)
        elif action=='revoke':
            obj=get_object_or_404(ParticipantPass.objects.select_for_update(),pk=request.data.get('id'),participant__event=member.event)
            reason=str(request.data.get('reason','')).strip()
            if not reason:raise ValidationError('Informe o motivo da revogação.')
            if not obj.revoked_at:
                obj.revoked_at=timezone.now();obj.revoked_by=request.user;obj.revocation_reason=reason;obj.save()
                record(request.user,'pass.revoked',obj,member.event,reason=reason)
        else:raise ValidationError('Ação inválida.')
        return Response({'ok':True})


class FinancialReportView(APIView):
    def get(self,request):
        member=access(request,admin=True)
        passes=ParticipantPass.objects.filter(participant__event=member.event).select_related('offer__pass_type','granted_by')
        return Response({'total':str(passes.aggregate(total=Sum('sale_amount'))['total'] or Decimal(0)),
            'sales':[{'id':str(p.pk),'type':p.offer_name or p.offer.pass_type.name,'amount':str(p.sale_amount),'free':p.sale_amount==0,
                'operator':p.granted_by.email if p.granted_by else 'Histórico','created':p.created_at,'revoked':p.revoked_at,'reason':p.revocation_reason} for p in passes],
            'notice':'Venda declarada no sistema; não comprova recebimento. Revogação preserva o lançamento original.'})
