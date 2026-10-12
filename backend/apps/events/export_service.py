import logging
import os
import shutil
import textwrap
import zipfile
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import transaction, connection
from django.utils import timezone

from apps.audit.services import record
from .models import ExportJob
from .export_snapshot import collect, digest, dump, sql_snapshot


def backup_root():
    root = Path(getattr(settings, 'EXPORT_BACKUP_ROOT', settings.BASE_DIR / 'backups'))
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def artifact(job, name):
    return backup_root() / str(job.pk) / name


def pdf_document(lines):
    """Portable, paginated PDF with WinAnsi text, no external service required."""
    wrapped = [part for line in lines for part in (textwrap.wrap(str(line), 95) or [''])]
    pages = [wrapped[i:i + 48] for i in range(0, len(wrapped), 48)]
    objects = [b'', b'', b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']
    kids = []
    for page in pages:
        page_id = len(objects) + 1
        content_id = page_id + 1
        kids.append(f'{page_id} 0 R')
        commands = ['BT /F1 10 Tf 48 790 Td 14 TL']
        for line in page:
            text = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            commands.append(f'({text}) Tj T*')
        commands.append('ET')
        content = '\n'.join(commands).encode('cp1252', errors='replace')
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>'.encode())
        objects.append(f'<< /Length {len(content)} >>\nstream\n'.encode() + content + b'\nendstream')
    objects[0] = b'<< /Type /Catalog /Pages 2 0 R >>'
    objects[1] = f'<< /Type /Pages /Count {len(pages)} /Kids [{" ".join(kids)}] >>'.encode()
    result = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f'{index} 0 obj\n'.encode() + obj + b'\nendobj\n')
    offset = len(result)
    result.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    for position in offsets[1:]:
        result.extend(f'{position:010} 00000 n \n'.encode())
    result.extend(f'trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{offset}\n%%EOF'.encode())
    return bytes(result)


def progress(job, amount, stage):
    ExportJob.objects.filter(pk=job.pk, state='PROCESSING').update(progress=amount, stage=stage, updated_at=timezone.now())


def export_lock_key(identifier):
    return int(str(identifier).replace('-', '')[:15], 16)


def generate_export(identifier):
    # Session lock survives short transactions and is released on worker death.
    locked = connection.vendor == 'postgresql'
    if locked:
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_try_advisory_lock(%s)', [export_lock_key(identifier)])
            if not cursor.fetchone()[0]:
                return 'PROCESSING'
    try:
        return _generate_export(identifier)
    except Exception:
        # Failed operational status must remain visible even when mandatory audit
        # prevented the start/completion transaction. Never publish success.
        ExportJob.objects.filter(pk=identifier).exclude(state='COMPLETED').update(state='FAILED',
            stage='Falha na exportação', error='Não foi possível gerar a exportação. Tente novamente.',
            finished_at=timezone.now(), updated_at=timezone.now())
        raise
    finally:
        if locked:
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_advisory_unlock(%s)', [export_lock_key(identifier)])


def _generate_export(identifier):
    with transaction.atomic():
        job = ExportJob.objects.select_for_update().select_related('event__organization', 'requested_by').get(pk=identifier)
        if job.state != 'PENDING':
            return job.state
        if not job.requested_by.is_active or not job.requested_by.is_superuser:
            job.state, job.error = 'FAILED', 'O solicitante não possui mais autorização para exportar.'
            job.save()
            record(None, 'export.failed', job, job.event)
            return job.state
        job.state, job.progress, job.stage = 'PROCESSING', 5, 'Coletando fotografia do evento'
        job.attempts += 1
        job.started_at = timezone.now()
        job.error = ''
        job.save()
        record(job.requested_by, 'export.started', job, job.event, attempt=job.attempts)
    destination = work = None
    try:
        destination = artifact(job, 'event.zip').parent
        work = destination / 'working'
        destination.mkdir(mode=0o700, parents=True, exist_ok=True)
        if work.exists():
            shutil.rmtree(work)
        work.mkdir()
        snapshot = collect(job.event, job.modules, work)
        event_data = snapshot['records']['events.event'][0]
        organization_data = snapshot['records']['organizations.organization'][0]
        progress(job, 35, 'Preparando SQL e interface offline')
        (work / 'snapshot.json').write_text(dump(snapshot), encoding='utf-8')
        (work / 'event.sql').write_text(sql_snapshot(snapshot), encoding='utf-8')
        template = Path(__file__).with_name('export_offline.html').read_text(encoding='utf-8')
        (work / 'index.html').write_text(template.replace('__SNAPSHOT__', dump(snapshot).replace('<', '\\u003c')), encoding='utf-8')
        (work / 'README.txt').write_text(
            'Abra index.html no navegador, sem servidor e sem rede. Interface somente leitura.\n'
            'Para consultar o SQL em um banco PostgreSQL vazio: psql --set ON_ERROR_STOP=1 --file event.sql\n'
            'As tabelas ficam no schema event_export, sem credenciais ou triggers de produção.\n'
            'snapshot.json registra relações entre as tabelas. Não restaure este pacote sobre produção.\n'
            'Verifique SHA-256 dos arquivos conforme manifest.json. O termo PDF é externo ao ZIP.\n', encoding='utf-8')
        (work / 'verify.py').write_text(
            'import hashlib, json\nfrom pathlib import Path\n'
            'root = Path(__file__).resolve().parent\n'
            'manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))\n'
            'for name, info in manifest["files"].items():\n'
            '    path = (root / name).resolve()\n'
            '    if not path.is_relative_to(root) or not path.is_file(): raise SystemExit("Missing or invalid file: " + name)\n'
            '    with path.open("rb") as stream: actual = hashlib.file_digest(stream, "sha256").hexdigest()\n'
            '    if actual != info["sha256"]: raise SystemExit("Invalid SHA-256: " + name)\n'
            'print("All manifest component hashes verified.")\n', encoding='utf-8')
        files = {str(p.relative_to(work)).replace('\\', '/'): {'sha256': digest(p), 'bytes': p.stat().st_size} for p in sorted(work.rglob('*')) if p.is_file()}
        manifest = {'formatVersion': 1, 'exportId': str(job.pk), 'eventId': str(job.event_id),
            'eventName': event_data['name'], 'organization': organization_data['name'],
            'generatedAt': timezone.now().isoformat(), 'snapshotAt': snapshot['capturedAt'],
            'systemVersion': os.getenv('APP_VERSION', 'development'),
            'requestedBy': str(job.requested_by_id), 'reference': job.reference,
            'modules': job.modules, 'mode': 'complete' if len(job.modules) == 10 else 'custom',
            'counts': {label: len(rows) for label, rows in snapshot['records'].items()},
            'omittedModules': snapshot['omittedModules'], 'missingMedia': snapshot['missingMedia'],
            'legalHolds': snapshot['records'].get('retention.legalhold', []),
            'minimization': 'Sem senhas, sessões, tokens, dados globais de privacidade ou outros eventos. Dependências relacionais identificadas no snapshot.',
            'retentionNotice': 'Somente registros ainda existentes na fotografia; dados eliminados/anonimizados não são reconstruídos. Arquivamento não substitui Legal Hold.',
            'readOnly': True, 'files': files}
        (work / 'manifest.json').write_text(dump(manifest), encoding='utf-8')
        progress(job, 65, 'Compactando e verificando integridade')
        temporary_zip = destination / 'event.zip.tmp'
        with zipfile.ZipFile(temporary_zip, 'w', zipfile.ZIP_DEFLATED) as package:
            for path in sorted(work.rglob('*')):
                if path.is_file():
                    package.write(path, path.relative_to(work))
        os.replace(temporary_zip, destination / 'event.zip')
        zip_hash = digest(destination / 'event.zip')
        progress(job, 90, 'Gerando termo de integridade')
        term = pdf_document([
            'TERMO DE EXPORTAÇÃO E INTEGRIDADE', f'Exportação: {job.pk}',
            f'Evento: {event_data["name"]} ({job.event_id})', f'Organização: {organization_data["name"]}',
            f'Início: {event_data["starts_at"]} / Encerramento: {event_data["closed_at"] or event_data["ends_at"]}',
            f'Gerado em UTC: {manifest["generatedAt"]}',
            f'Responsável: {job.requested_by.get_full_name()} / {job.requested_by.email}',
            f'Referência: {job.reference or "Geração para testes pela administração global"}',
            f'Versão do sistema: {manifest["systemVersion"]}', f'Modalidade: {manifest["mode"]}',
            'Módulos: ' + ', '.join(job.modules), 'Arquivo: event.zip / algoritmo: SHA-256', zip_hash,
            'Conteúdo: event.sql, index.html (SPA offline), snapshot.json, manifest.json e mídias disponíveis.',
            'Resumo dos registros: ' + dump(manifest['counts']),
            'Legal Holds vinculados: ' + str(len(manifest['legalHolds'])),
            'Arquivos indisponíveis: ' + str(len(manifest['missingMedia'])),
            manifest['retentionNotice'], manifest['minimization'],
            'A SPA é somente leitura, sem operações administrativas e sem comunicação com produção.',
            'Este PDF é externo ao ZIP para evitar circularidade do hash.',
            'Termo ainda NÃO ASSINADO. Assinatura eletrônica e encaminhamento devem ser registrados separadamente.',
        ])
        (destination / 'term.pdf').write_bytes(term)
        for name in ['event.zip', 'term.pdf']:
            os.chmod(destination / name, 0o600)
        with transaction.atomic():
            job = ExportJob.objects.select_for_update().get(pk=identifier)
            job.state, job.progress, job.stage = 'COMPLETED', 100, 'Exportação concluída'
            job.finished_at = timezone.now()
            ttl = getattr(settings, 'EXPORT_DOWNLOAD_TTL_HOURS', 168)
            job.expires_at = job.finished_at + timedelta(hours=ttl) if ttl else None
            job.zip_path, job.pdf_path = str(Path(str(job.pk)) / 'event.zip'), str(Path(str(job.pk)) / 'term.pdf')
            job.zip_sha256, job.pdf_sha256, job.manifest = zip_hash, digest(destination / 'term.pdf'), manifest
            job.save()
            record(job.requested_by, 'export.completed', job, job.event, sha256=zip_hash, modules=job.modules)
        return 'COMPLETED'
    except Exception:
        logging.getLogger(__name__).exception('Export generation failed for %s', identifier)
        if destination:
            for name in ['event.zip', 'event.zip.tmp', 'term.pdf']:
                (destination / name).unlink(missing_ok=True)
        with transaction.atomic():
            job = ExportJob.objects.select_for_update().get(pk=identifier)
            job.state, job.stage, job.error = 'FAILED', 'Falha na exportação', 'Não foi possível gerar a exportação. Tente novamente.'
            job.finished_at = timezone.now()
            job.save()
            record(None, 'export.failed', job, job.event)
        raise
    finally:
        if work and work.exists():
            shutil.rmtree(work)
