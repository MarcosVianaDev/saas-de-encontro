from django.urls import path
from .consumers import RealtimeConsumer

websocket_urlpatterns = [
    path('ws/global/', RealtimeConsumer.as_asgi(), {'context': 'global'}),
    path('ws/events/<uuid:event_id>/participant/', RealtimeConsumer.as_asgi(), {'context': 'participant'}),
    path('ws/events/<uuid:event_id>/administration/', RealtimeConsumer.as_asgi(), {'context': 'administration'}),
]
