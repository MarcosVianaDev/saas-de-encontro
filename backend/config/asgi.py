import os
from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_application = get_asgi_application()

from realtime.middleware import WebsocketOriginValidator
from realtime.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_application,
    'websocket': WebsocketOriginValidator(AuthMiddlewareStack(URLRouter(websocket_urlpatterns))),
})
