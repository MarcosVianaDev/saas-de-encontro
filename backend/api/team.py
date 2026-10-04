from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.events.models import EventAdministrator
from apps.events.permissions import OPERATIONAL, effective_role
from apps.events.services import notify_managers
from apps.audit.services import record
from .event_admin import access


class TeamView(APIView):
    def get(self,request):
        member = access(request,admin=True)
        return Response({'canAssignAdministrator':request.user.is_superuser,'permissions':sorted(OPERATIONAL),'members':[{'id':str(m.pk),'user':str(m.user_id),
            'email':m.user.email,'name':m.user.get_full_name() or m.user.email,'role':m.role,'active':m.is_active,
            'permissions':m.permissions,'delegatedTo':str(m.delegated_to_id) if m.delegated_to_id else None}
            for m in member.event.administrators.select_related('user').all()]})

    @transaction.atomic
    def post(self,request):
        action = request.data.get('action','save')
        if action == 'reclaim':
            member = get_object_or_404(EventAdministrator.objects.select_for_update(),user=request.user,event_id=request.session.get('event_id'),is_active=True,role='ADMIN')
            member.delegated_to = None; member.save()
            record(request.user,'team.reclaimed',member,member.event)
            notify_managers(member.event,'Administração retomada','A gestão original reassumiu o evento.')
            return Response({'ok':True})
        member = access(request,admin=True)
        if member.event.state in ['CLOSED','ARCHIVED']:
            raise PermissionDenied('Equipe em modo somente leitura após o encerramento.')
        if action == 'delegate':
            if request.data.get('confirmed') is not True: raise ValidationError('Confirme a transferência temporária.')
            owner=member.event.responsible if request.user.is_superuser else request.user
            original = get_object_or_404(EventAdministrator.objects.select_for_update(),event=member.event,user=owner,role='ADMIN',is_active=True)
            target = get_object_or_404(EventAdministrator,event=member.event,pk=request.data.get('id'),role='MODERATOR',is_active=True)
            original.delegated_to = target.user; original.save()
            record(request.user,'team.delegated',original,member.event,to=str(target.user_id))
            notify_managers(member.event,'Administração transferida',f'Administração delegada temporariamente a {target.user.get_full_name() or target.user.email}.')
        elif action == 'save':
            user = get_object_or_404(get_user_model(),email=request.data.get('email'),is_active=True)
            role = request.data.get('role')
            permissions = request.data.get('permissions',[])
            if role not in ['ADMIN','MODERATOR','OPERATOR'] or not isinstance(permissions,list) or set(permissions)-OPERATIONAL:
                raise ValidationError('Papel ou permissões inválidos.')
            if role == 'ADMIN' and not request.user.is_superuser:
                raise PermissionDenied('A gestão global define o Administrador do Evento; use a delegação temporária para Moderadores.')
            target,created = EventAdministrator.objects.get_or_create(event=member.event,user=user,defaults={'role':role})
            if target.role == 'ADMIN' and not request.user.is_superuser:
                raise PermissionDenied('Não é permitido revogar a gestão responsável.')
            target.role=role; target.permissions=permissions; target.is_active=request.data.get('active',True) is True; target.save()
            from django.contrib.auth.models import Group
            for group_name,group_role in [('Moderador','MODERATOR'),('Operador','OPERATOR')]:
                if not user.event_administrations.filter(is_active=True,role=group_role).exists():
                    user.groups.remove(*Group.objects.filter(name=group_name))
            if role in ['MODERATOR','OPERATOR'] and target.is_active:
                group,_=Group.objects.get_or_create(name='Moderador' if role=='MODERATOR' else 'Operador')
                user.groups.add(group)
            record(request.user,'team.changed',target,member.event,role=role,permissions=permissions,active=target.is_active)
        else: raise ValidationError('Ação inválida.')
        return Response({'ok':True})
