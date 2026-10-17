"""Authorize delivery of compiled frontends independently of API permissions."""
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


def allowed(user, audience):
    if not user.is_authenticated or not user.is_active:
        return False
    if audience not in ('participant', 'event-manager', 'global'):
        return False
    if user.is_superuser:
        return True
    if audience == 'event-manager':
        return user.event_administrations.filter(is_active=True).exists()
    if audience == 'participant':
        return user.event_participations.exists()
    return False


@never_cache
@require_GET
def authorize(request):
    # Use Django's authenticated session, never a role supplied by the browser.
    if not request.user.is_authenticated:
        return HttpResponse(status=401)
    return HttpResponse(status=204 if allowed(request.user, request.GET.get('audience')) else 403)


@never_cache
@api_view(['GET'])
@permission_classes([AllowAny])
def route(request):
    if not request.user.is_authenticated:
        return JsonResponse({'audience': 'login', 'path': '/'})
    from .event_admin import navigation
    from .event_scope import navigation_context
    # Restore legacy sessions using the same rules as login/bootstrap.
    if navigation_context(request) == 'selection' and 'X-App-Context' not in request.headers:
        from .contexts import administration_context, select
        context = administration_context(request.user)
        if context:
            select(request, context['key'])
    data = navigation(request)
    nav = data['navigation']
    audience = ('global' if request.user.is_superuser else
                'event-manager' if nav == 'administration' else
                'login' if nav == 'selection' else 'participant')
    if audience != 'login' and not allowed(request.user, audience):
        return HttpResponse(status=403)
    page = ('admin-' + data.get('initialPage', 'dashboard') if nav == 'administration'
            else 'perfil' if nav == 'participant' else '')
    path = '/' if audience == 'login' else f'/spa/{audience}/'
    return JsonResponse({'audience': audience, 'path': path + ('#' + page if page else '')})
