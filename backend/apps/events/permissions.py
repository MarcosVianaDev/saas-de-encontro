from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from .models import EventAdministrator

OPERATIONAL = {'reports', 'blocks', 'passes', 'activation', 'outfit', 'remove_photo', 'edit_bio', 'location_exception', 'announcements'}
DEFAULTS = {'ADMIN': OPERATIONAL, 'MODERATOR': {'reports','blocks','activation','outfit','remove_photo','edit_bio','location_exception','announcements'},
    'OPERATOR': {'activation','outfit'}}


def effective_role(member):
    if member.user.is_superuser:
        return 'ADMIN'
    if EventAdministrator.objects.filter(event=member.event, is_active=True, delegated_to=member.user).exists():
        return 'ADMIN'
    if member.delegated_to_id:
        return 'DELEGATED'
    return member.role


def permits(member, permission):
    role = effective_role(member)
    return permission in DEFAULTS.get(role, set()) or permission in member.permissions


def require(member, permission):
    if not permits(member, permission):
        raise PermissionDenied('Seu papel não possui a permissão operacional necessária.')
