from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.events.models import Event, EventAdministrator


def available(user):
    contexts = []
    if user.is_superuser:
        contexts.append({'key':'global','navigation':'global','name':'Administração Global'})
    for p in user.event_participations.select_related('event').order_by('created_at'):
        contexts.append({'key':f'participant:{p.event_id}','navigation':'participant','event':str(p.event_id),'name':p.event.name})
    for m in user.event_administrations.filter(is_active=True).select_related('event').order_by('created_at'):
        contexts.append({'key':f'administration:{m.event_id}','navigation':'administration','event':str(m.event_id),'name':m.event.name+' — Administração'})
    return contexts


def select(request, key):
    context = next((c for c in available(request.user) if c['key'] == key),None)
    if not context:
        raise PermissionDenied('Este contexto não está disponível para sua conta.')
    request.session['navigation'] = context['navigation']
    if context.get('event'): request.session['event_id'] = context['event']
    else: request.session.pop('event_id',None)
    return context


def administration_context(user):
    return next((context for context in available(user) if context['navigation'] in ['global', 'administration']), None)


class ContextView(APIView):
    def get(self,request):
        context = administration_context(request.user)
        if context:
            select(request, context['key'])
            from .views import login_payload
            return Response(login_payload(request))
        return Response({'navigation':'selection','contexts':available(request.user)})

    def post(self,request):
        select(request,request.data.get('key'))
        from .views import login_payload
        return Response(login_payload(request))


class GlobalEventContextView(APIView):
    def post(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied('Acesso exclusivo da Administração Global.')
        event = get_object_or_404(Event,pk=request.data.get('event'))
        request.session['event_id'] = str(event.pk)
        request.session['navigation'] = 'administration'
        return Response({'navigation':'administration','role':'ADMIN','globalContext':True,
            'initialPage': 'event' if event.state == 'DRAFT' else 'dashboard'})
