#!/usr/bin/env bash
# Recria o banco do Compose na VPS. Nao cria usuarios nem dados demo.
set -Eeuo pipefail

usage() {
    printf 'Uso: bash zerar-banco.sh [--force]\n'
}

force=false
case "${1:-}" in
    '') ;;
    --force|-f) force=true ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
esac
if (( $# > 1 )); then
    usage >&2
    exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$script_dir"

on_error() {
    local status=$?
    printf '\nFalha ao zerar o banco (codigo %s). Os servicos podem estar parados; corrija o erro e execute novamente.\n' "$status" >&2
    exit "$status"
}
trap on_error ERR

if [[ ! -f .env ]]; then
    printf 'Crie o .env a partir do .env.example antes de executar.\n' >&2
    exit 1
fi
command -v python3 >/dev/null
docker compose version
printf '%s\n' \
    'ATENCAO: todos os cadastros, usuarios, sessoes e registros de auditoria serao apagados.' \
    'O Redis do projeto tambem sera esvaziado. Fotos em backend/media serao preservadas.'
if [[ "$force" != true ]]; then
    answer=''
    read -r -p 'Digite ZERAR para confirmar: ' answer || true
    if [[ "$answer" != ZERAR ]]; then
        printf 'Operacao cancelada.\n'
        exit 0
    fi
fi

# Persiste o modo manual para as proximas inicializacoes do ambiente.
python3 - <<'PY'
from pathlib import Path
import re

path = Path('.env')
text = path.read_text(encoding='utf-8-sig')
for entry in ('DJANGO_SEED_DEMO=0', 'FRONTEND_DATA_MODE=django'):
    key = entry.split('=', 1)[0]
    pattern = rf'(?m)^[ \t]*{key}[ \t]*=.*$'
    if re.search(pattern, text):
        text = re.sub(pattern, entry, text)
    else:
        text = text.rstrip() + '\n' + entry + '\n'
path.write_text(text, encoding='utf-8')
PY

# Impede escritas e tarefas enquanto o schema e recriado.
docker compose stop backend celery_worker celery_beat
docker compose up -d --wait db redis
docker compose exec -T redis redis-cli FLUSHALL

docker compose run --rm --no-deps -T backend python - <<'PY'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.core.management import call_command
from django.db import connection, transaction
from django.contrib.auth import get_user_model

if connection.vendor != 'postgresql':
    raise RuntimeError('Este script exige o PostgreSQL do projeto.')
if connection.settings_dict['HOST'] != 'db':
    raise RuntimeError('POSTGRES_HOST deve ser db: reset permitido apenas no banco deste Compose.')

with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute('DROP SCHEMA public CASCADE')
        cursor.execute('CREATE SCHEMA public')
call_command('migrate', interactive=False)
if get_user_model().objects.exists():
    raise RuntimeError('O banco ainda possui usuarios apos a limpeza.')
print('Banco recriado, migracoes aplicadas e nenhum usuario cadastrado.')
PY

docker compose up -d --force-recreate --wait backend celery_worker celery_beat frontend nginx traefik
printf '\n%s\n' \
    'Pronto! Crie seu primeiro administrador:' \
    'docker compose exec backend python manage.py createsuperuser' \
    'Depois, acesse /admin/ no endereco da sua VPS (na porta configurada no .env).' \
    'Recarregue o navegador para descartar a sessao anterior.'
