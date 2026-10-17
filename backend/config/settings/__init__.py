import os
from pathlib import Path
from kombu import Queue
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.getenv("DJANGO_DEBUG", "0").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [host.strip() for host in os.getenv(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]" if DEBUG else "",
).split(",") if host.strip()]
if not DEBUG and (not ALLOWED_HOSTS or any('*' in host for host in ALLOWED_HOSTS)):
    raise ImproperlyConfigured('Em produção, defina DJANGO_ALLOWED_HOSTS com hosts explícitos, sem *.')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080" if DEBUG else "",
).split(",") if origin.strip()]
INSTALLED_APPS = [
    "config.apps.SecureAdminConfig", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "channels", "realtime.apps.RealtimeConfig",
    *[f"apps.{name}" for name in (
        "accounts", "organizations", "events", "rooms", "participants", "profiles",
        "discovery", "interactions", "matches", "messaging", "passes", "payments",
        "reports", "moderation", "consent", "retention", "audit", "notifications", "analytics",
    )],
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
LOGIN_URL = '/mcx/login/'
LOGIN_REDIRECT_URL = '/mcx/'
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"django.contrib.auth.password_validation.{name}"} for name in (
        "UserAttributeSimilarityValidator", "MinimumLengthValidator", "CommonPasswordValidator", "NumericPasswordValidator",
    )
]
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ["POSTGRES_DB"], "USER": os.environ["POSTGRES_USER"],
    "PASSWORD": os.environ["POSTGRES_PASSWORD"], "HOST": os.getenv("POSTGRES_HOST", "db"),
    "PORT": os.getenv("POSTGRES_PORT", "5432"),
}}
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": os.getenv("DJANGO_CACHE_URL", "redis://redis:6379/2"),
    "KEY_PREFIX": os.getenv("DJANGO_CACHE_KEY_PREFIX", "eventconnect"),
}}
TEST_RUNNER = "config.testing.IsolatedCacheTestRunner"
CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": {
    "hosts": [REDIS_URL],
    "prefix": os.getenv('CHANNEL_REDIS_PREFIX', CACHES['default']['KEY_PREFIX'] + ':channels'),
    "expiry": 60,
}}}
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
# Keep the existing default queue so pending operational tasks remain consumable.
# Export/gift workers consume dedicated queues; operational workers never reserve them.
CELERY_TASK_DEFAULT_QUEUE = 'celery'
CELERY_TASK_QUEUES = (Queue('celery'), Queue('exports'), Queue('gifts'))
CELERY_TASK_ROUTES = {
    'apps.events.export_tasks.generate': {'queue': 'exports'},
    'apps.passes.tasks.initial_gift_batch': {'queue': 'gifts'},
}
INITIAL_GIFT_BATCH_SIZE = int(os.getenv('INITIAL_GIFT_BATCH_SIZE', '25'))
if not 1 <= INITIAL_GIFT_BATCH_SIZE <= 100:
    raise ImproperlyConfigured('INITIAL_GIFT_BATCH_SIZE deve estar entre 1 e 100.')
CELERY_BEAT_SCHEDULE = {
    'initial-gifts': {'task': 'apps.passes.tasks.initial_gifts', 'schedule': 30.0},
    'event-lifecycle': {'task': 'apps.events.tasks.synchronize_events', 'schedule': 30.0},
    'pass-expiration': {'task':'apps.passes.tasks.expire','schedule':30.0},
    'scheduled-announcements': {'task':'apps.notifications.tasks.dispatch_announcements','schedule':30.0},
}
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
# The backend must only be reachable through trusted proxies that overwrite
# this header. Disable trust when deploying directly without a reverse proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if os.getenv(
    "DJANGO_TRUST_PROXY_SSL_HEADER", "1",
).lower() in {"1", "true", "yes"} else None
X_FRAME_OPTIONS = "DENY"
MEDIA_ROOT = BASE_DIR / "media"
# Compose enables this behind Nginx. Direct Django/Vite development can opt out.
MEDIA_USE_X_ACCEL_REDIRECT = os.getenv('MEDIA_USE_X_ACCEL_REDIRECT', '0').lower() in {'1', 'true', 'yes'}
EXPORT_DOWNLOAD_TTL_HOURS = int(os.getenv('EXPORT_DOWNLOAD_TTL_HOURS', '168'))
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER':'api.exceptions.exception_handler',
    "DEFAULT_AUTHENTICATION_CLASSES": ["api.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["api.permissions.AccountAccess"],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "api.throttling.WriteScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DRF_THROTTLE_ANON", "60/min"),
        "user": os.getenv("DRF_THROTTLE_USER", "300/min"),
        "login": os.getenv("DRF_THROTTLE_LOGIN", "10/min"),
        "register": os.getenv("DRF_THROTTLE_REGISTER", "5/min"),
        "messages": os.getenv("DRF_THROTTLE_MESSAGES", "30/min"),
        "interactions": os.getenv("DRF_THROTTLE_INTERACTIONS", "60/min"),
        "reports": os.getenv("DRF_THROTTLE_REPORTS", "10/min"),
    },
    # Compose exposes the backend only through Traefik -> Nginx. Use 0 when
    # serving directly, and adjust this count if the trusted proxy chain changes.
    "NUM_PROXIES": int(os.getenv("DRF_NUM_PROXIES", "2")),
}
DEMO_USER_EMAIL = os.getenv("DEMO_USER_EMAIL", "demo@eventconnect.local")
DEMO_USER_PASSWORD = os.getenv("DEMO_USER_PASSWORD", "")
ADMIN_LOGIN_IP_LIMIT = int(os.getenv('DJANGO_ADMIN_LOGIN_IP_LIMIT', '5'))
ADMIN_LOGIN_ACCOUNT_LIMIT = int(os.getenv('DJANGO_ADMIN_LOGIN_ACCOUNT_LIMIT', '10'))
ADMIN_LOGIN_WINDOW_SECONDS = int(os.getenv('DJANGO_ADMIN_LOGIN_WINDOW_SECONDS', '300'))
if min(ADMIN_LOGIN_IP_LIMIT, ADMIN_LOGIN_ACCOUNT_LIMIT, ADMIN_LOGIN_WINDOW_SECONDS) < 1:
    raise ImproperlyConfigured('Os limites de login administrativo devem ser positivos.')
