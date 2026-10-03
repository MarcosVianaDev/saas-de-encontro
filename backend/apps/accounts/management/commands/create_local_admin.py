"""Provisionamento local via JSON em stdin, sem credenciais nos argumentos."""
import json
import sys
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Cria um administrador local com credenciais recebidas por stdin."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Comando disponível somente com DEBUG=1.")
        credentials = json.load(sys.stdin)
        User = get_user_model()
        if User.objects.filter(username=credentials["username"]).exists():
            raise CommandError("Usuário já existe; nenhuma senha foi alterada.")
        validate_password(credentials["password"])
        User.objects.create_superuser(**credentials)
        self.stdout.write(self.style.SUCCESS("Administrador local criado."))
