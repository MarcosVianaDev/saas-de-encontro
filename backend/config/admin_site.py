import logging
import time
import unicodedata

from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.decorators import login_not_required
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils.crypto import salted_hmac
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework.throttling import BaseThrottle

from common.security import account_allowed


class SecureAdminAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not account_allowed(user):
            raise ValidationError('Não foi possível entrar com estas credenciais.', code='invalid_login')


def login_retry_after(request):
    """Shared, atomic fixed-window budgets; never store usernames/IPs in keys."""
    window = settings.ADMIN_LOGIN_WINDOW_SECONDS
    now = int(time.time())
    bucket = now // window
    ident = BaseThrottle().get_ident(request) or 'unknown'
    username = unicodedata.normalize('NFKC', request.POST.get('username', '')).strip().casefold()
    budgets = [('ip', ident, settings.ADMIN_LOGIN_IP_LIMIT)]
    if username:
        budgets.append(('account', username, settings.ADMIN_LOGIN_ACCOUNT_LIMIT))
    for kind, value, limit in budgets:
        digest = salted_hmac('admin-login-' + kind, value).hexdigest()
        key = f'admin-login:{kind}:{bucket}:{digest}'
        if cache.add(key, 1, timeout=window + 1):
            count = 1
        else:
            try:
                count = cache.incr(key)
            except ValueError:
                # A key can expire between add() and incr(). Never fail open.
                if cache.add(key, 1, timeout=window + 1):
                    count = 1
                else:
                    count = cache.incr(key)
        if count > limit:
            return window - now % window
    return 0


class SecureAdminSite(AdminSite):
    login_form = SecureAdminAuthenticationForm

    def has_permission(self, request):
        return super().has_permission(request) and account_allowed(request.user)

    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    @method_decorator(sensitive_post_parameters('password'))
    @login_not_required
    def login(self, request, extra_context=None):
        if request.method == 'POST':
            try:
                retry = login_retry_after(request)
            except Exception:
                logging.getLogger(__name__).exception('Limitador do login administrativo indisponível')
                return HttpResponse('Acesso temporariamente indisponível. Tente novamente.', status=503)
            if retry:
                response = HttpResponse('Muitas tentativas de login. Aguarde e tente novamente.', status=429)
                response['Retry-After'] = str(retry)
                return response
        return super().login(request, extra_context)
