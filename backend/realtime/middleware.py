from channels.security.websocket import OriginValidator
from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.http import HttpRequest


class WebsocketOriginValidator:
    """Require an explicit trusted Origin, including in DEBUG; never allow '*'."""

    def __init__(self, application):
        self.application = application

    async def __call__(self, scope, receive, send):
        headers = dict(scope.get('headers', []))
        request = HttpRequest()
        request.META['HTTP_HOST'] = headers.get(b'host', b'').decode('latin1')
        try:
            host = request.get_host()
            schemes = ['https', 'http'] if settings.DEBUG else ['https']
            origins = [f'{scheme}://{host}' for scheme in schemes]
            origins += [origin for origin in settings.CSRF_TRUSTED_ORIGINS if origin != '*'
                        and (settings.DEBUG or origin.startswith('https://'))]
        except DisallowedHost:
            origins = []
        return await OriginValidator(self.application, origins)(scope, receive, send)
