from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.notifications.models import SupportThread,SupportMessage
from apps.notifications.services import notify
from apps.events.services import notify_managers
from apps.audit.services import record
from .services import current
from .event_admin import access


def payload(thread):
    return {'id':str(thread.pk),'participant':str(thread.participant_id),'subject':thread.subject,
        'messages':[{'id':str(m.pk),'body':m.body,'author':m.author.get_full_name() or m.author.email,'mine':m.author_id==thread.participant.user_id,'created':m.created_at} for m in thread.messages.select_related('author').order_by('created_at')]}


class SupportView(APIView):
    def get(self,request):
        p=current(request);return Response([payload(t) for t in p.support_threads.all()])

    @transaction.atomic
    def post(self,request):
        p=current(request);body=str(request.data.get('body','')).strip()
        if not body or len(body)>4000:raise ValidationError('Escreva sua solicitação (até 4.000 caracteres).')
        thread=get_object_or_404(SupportThread,pk=request.data['thread'],participant=p) if request.data.get('thread') else SupportThread.objects.create(participant=p,subject=str(request.data.get('subject','Suporte'))[:200])
        message=SupportMessage.objects.create(thread=thread,author=request.user,body=body)
        record(request.user,'support.requested',message,p.event)
        notify_managers(p.event,'Nova solicitação de suporte',thread.subject)
        return Response(payload(thread),status=201)


class AdminSupportView(APIView):
    def get(self,request):
        member=access(request,moderate=True)
        return Response([payload(t) for t in SupportThread.objects.filter(participant__event=member.event)])

    @transaction.atomic
    def post(self,request):
        member=access(request,moderate=True)
        thread=get_object_or_404(SupportThread,pk=request.data.get('thread'),participant__event=member.event)
        body=str(request.data.get('body','')).strip()
        if not body or len(body)>4000:raise ValidationError('Escreva a resposta (até 4.000 caracteres).')
        message=SupportMessage.objects.create(thread=thread,author=request.user,body=body)
        record(request.user,'support.replied',message,member.event)
        notify(thread.participant,'support','A equipe respondeu ao seu atendimento',body,action_path='#mensagens')
        return Response(payload(thread),status=201)
