"""Inicialização do servidor: migrações, dados de DEBUG e arquivos estáticos."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.conf import settings
from django.core.management import call_command

call_command("migrate", interactive=False)
if settings.DEBUG:
    call_command("seed_demo")
call_command("collectstatic", interactive=False)
os.execvp("daphne", ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"])
