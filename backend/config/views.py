import django
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from redis import Redis


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        Redis.from_url(settings.REDIS_URL).ping()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "django": django.get_version(), "postgresql": "ok", "redis": "ok"})
