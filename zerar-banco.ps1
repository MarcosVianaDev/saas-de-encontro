# Recria o banco local para testes manuais. Nao cria usuarios nem dados demo.
[CmdletBinding()]
param([switch]$Force)

$ErrorActionPreference = 'Stop'

function Invoke-Compose {
    param([string[]]$ComposeArgs)
    & docker compose @ComposeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose falhou (codigo $LASTEXITCODE). Os servicos podem estar parados; corrija o erro e execute o script novamente."
    }
}

Push-Location $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath '.env' -PathType Leaf)) {
        throw 'Crie o .env a partir do .env.example antes de executar.'
    }
    Invoke-Compose -ComposeArgs @('version')
    Write-Host 'ATENCAO: todos os cadastros, usuarios, sessoes e registros de auditoria serao apagados.' -ForegroundColor Yellow
    Write-Host 'O Redis do projeto tambem sera esvaziado. Fotos em backend/media serao preservadas.'
    if (-not $Force) {
        $answer = Read-Host 'Digite ZERAR para confirmar'
        if ($answer -cne 'ZERAR') {
            Write-Host 'Operacao cancelada.'
            return
        }
    }

    # Persiste o modo manual para as proximas inicializacoes do ambiente.
    $envPath = Join-Path $PSScriptRoot '.env'
    $envText = [System.IO.File]::ReadAllText($envPath)
    foreach ($entry in @('DJANGO_SEED_DEMO=0', 'FRONTEND_DATA_MODE=debug')) {
        $key = $entry.Split('=')[0]
        $pattern = "(?m)^\s*$key\s*=.*$"
        if ([regex]::IsMatch($envText, $pattern)) {
            $envText = [regex]::Replace($envText, $pattern, $entry)
        } else {
            $envText = $envText.TrimEnd() + "`r`n$entry`r`n"
        }
    }
    [System.IO.File]::WriteAllText($envPath, $envText, [System.Text.UTF8Encoding]::new($false))

    # Impede escritas e tarefas enquanto o schema e recriado.
    Invoke-Compose -ComposeArgs @('stop', 'backend', 'celery_worker', 'celery_beat')
    Invoke-Compose -ComposeArgs @('up', '-d', '--wait', 'db', 'redis')
    Invoke-Compose -ComposeArgs @('exec', '-T', 'redis', 'redis-cli', 'FLUSHALL')

    $resetCode = @'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()
from django.core.management import call_command
from django.db import connection, transaction
from django.contrib.auth import get_user_model

if connection.vendor != "postgresql":
    raise RuntimeError("Este script exige o PostgreSQL local do projeto.")
if connection.settings_dict["HOST"] != "db":
    raise RuntimeError("POSTGRES_HOST deve ser db: reset permitido apenas no Compose local.")

with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute("DROP SCHEMA public CASCADE")
        cursor.execute("CREATE SCHEMA public")
call_command("migrate", interactive=False)
if get_user_model().objects.exists():
    raise RuntimeError("O banco ainda possui usuarios apos a limpeza.")
print("Banco recriado, migracoes aplicadas e nenhum usuario cadastrado.")
'@
    $resetCode | & docker compose run --rm --no-deps -T backend python -
    if ($LASTEXITCODE -ne 0) {
        throw 'Falha ao recriar o banco. Os servicos continuam parados; corrija o erro e execute novamente.'
    }

    Invoke-Compose -ComposeArgs @('up', '-d', '--force-recreate', '--wait', 'backend', 'celery_worker', 'celery_beat', 'frontend', 'nginx', 'traefik')
    Write-Host ''
    Write-Host 'Pronto! Crie seu primeiro administrador:' -ForegroundColor Green
    Write-Host 'docker compose exec backend python manage.py createsuperuser'
    Write-Host 'Depois, acesse http://localhost:8080/admin/ (ou a porta configurada no .env).'
    Write-Host 'Recarregue o navegador para descartar a sessao anterior.'
} finally {
    Pop-Location
}
