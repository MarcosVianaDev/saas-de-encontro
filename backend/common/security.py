"""Account restrictions shared by HTTP, domain services and asset delivery."""
from django.db.models import Q
from django.utils import timezone


def suspended_user_ids():
    from apps.moderation.models import UserSuspension
    return UserSuspension.objects.filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now()),
    ).values('user_id')


def account_allowed(user):
    if not user or not user.is_authenticated or not user.is_active:
        return False
    return not user.suspensions.filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now()),
    ).exists()


def request_account_allowed(request):
    """Reuse the permission check only within this request and for this user."""
    user_id = getattr(request.user, 'pk', None)
    if user_id is not None and getattr(request, '_allowed_account_id', None) == user_id:
        return True
    if not account_allowed(request.user):
        return False
    request._allowed_account_id = user_id
    return True
