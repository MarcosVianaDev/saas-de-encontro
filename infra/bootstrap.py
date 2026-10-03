"""Bootstrap de infraestrutura, sem apps ou modelos de negocio."""
import os

from celery import Celery
from django.conf import settings

settings.configure(
    SECRET_KEY=os.environ["DJANGO_SECRET_KEY"],
    DEBUG=os.getenv("DJANGO_DEBUG", "0") == "1",
    ALLOWED_HOSTS=os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend").split(","),
    ROOT_URLCONF=__name__,
    INSTALLED_APPS=["rest_framework", "channels"],
    DATABASES={"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }},
    CHANNEL_LAYERS={"default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [os.environ["REDIS_URL"]]},
    }},
    MIDDLEWARE=[],
)

import django
django.setup()

from django.core.asgi import get_asgi_application
from django.db import connection
from django.http import JsonResponse
from django.urls import path
from redis import Redis
from channels.routing import ProtocolTypeRouter


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        Redis.from_url(os.environ["REDIS_URL"]).ping()
        return JsonResponse({"status": "ok", "django": django.get_version(), "postgresql": "ok", "redis": "ok"})
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)


urlpatterns = [path("api/health/", health)]
application = ProtocolTypeRouter({"http": get_asgi_application()})
celery_app = Celery("bootstrap", broker=os.environ["CELERY_BROKER_URL"])


@celery_app.task
def ping():
    return "pong"
