from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from .models import EventAdministrator
from common.security import account_allowed, suspended_user_ids

OPERATIONAL = {'reports', 'blocks', 'passes', 'activation', 'outfit', 'remove_photo', 'edit_bio', 'location_exception', 'announcements'}
DEFAULTS = {'ADMIN': OPERATIONAL, 'MODERATOR': {'reports','blocks','activation','outfit','remove_photo','edit_bio','location_exception','announcements'},
    'OPERATOR': {'activation','outfit'}}


def effective_role(member):
    if not getattr(member, 'is_active', True) or not account_allowed(member.user):
        return 'REVOKED'
    if member.user.is_superuser:
        return 'ADMIN'
    if member.role == 'MODERATOR' and EventAdministrator.objects.filter(
        event=member.event, is_active=True, role='ADMIN', delegated_to=member.user, user__is_active=True,
    ).exclude(user_id__in=suspended_user_ids()).exists():
        return 'ADMIN'
    if member.delegated_to_id and EventAdministrator.objects.filter(
        event=member.event, user_id=member.delegated_to_id, is_active=True, role='MODERATOR', user__is_active=True,
    ).exclude(user_id__in=suspended_user_ids()).exists():
        return 'DELEGATED'
    return member.role


def permits(member, permission):
    role = effective_role(member)
    if role == 'REVOKED':
        return False
    return permission in DEFAULTS.get(role, set()) or permission in member.permissions


def require(member, permission):
    if not permits(member, permission):
        raise PermissionDenied('Seu papel não possui a permissão operacional necessária.')
