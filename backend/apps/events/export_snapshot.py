"""Event ownership is derived only from event/participation and owned records.

Shared account/client/catalog records are dependencies, never traversal roots.
"""
import hashlib
import json
from pathlib import Path

from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.storage import default_storage
from django.core.exceptions import SuspiciousFileOperation
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone

MODULES = ['participants', 'moderation', 'messages', 'location', 'passes', 'notifications', 'rooms', 'metrics', 'consent', 'audit']
APP_MODULE = {'participants': 'participants', 'profiles': 'participants', 'discovery': 'participants',
    'interactions': 'participants', 'matches': 'messages', 'messaging': 'messages', 'reports': 'moderation',
    'moderation': 'moderation', 'passes': 'passes', 'payments': 'passes', 'notifications': 'notifications',
    'rooms': 'rooms', 'analytics': 'metrics', 'consent': 'consent', 'retention': 'consent'}
SHARED = {'accounts.user', 'organizations.organization', 'organizations.organizationmember',
    'profiles.profiletopic', 'passes.passtype'}
EXCLUDED = {'accounts.userprofile', 'moderation.usersuspension', 'retention.privacyrequest', 'events.exportjob'}


def dump(value):
    return json.dumps(value, cls=DjangoJSONEncoder, ensure_ascii=False, sort_keys=True)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def model_module(model):
    if model._meta.label_lower in ['participants.locationreading', 'participants.locationanomaly']:
        return 'location'
    return APP_MODULE.get(model._meta.app_label, 'participants')


def collect(event, modules, directory):
    """A repeatable-read DB snapshot; copy available media before leaving it."""
    outer_transaction = connection.in_atomic_block
    with transaction.atomic():
        if connection.vendor == 'postgresql' and not outer_transaction:
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        models = [m for m in apps.get_models() if m.__module__.startswith('apps.') and m._meta.label_lower not in EXCLUDED | SHARED and m._meta.app_label != 'audit']
        records = {event._meta.label_lower: {event.pk: type(event).objects.get(pk=event.pk)}}
        event = records[event._meta.label_lower][event.pk]
        captured_at = timezone.now().isoformat()
        # Select direct event records and recursively owned children. Never follow
        # a user, organization or shared catalog in the reverse direction.
        for _ in range(len(models) + 1):
            changed = False
            for model in models:
                label = model._meta.label_lower
                if label == 'events.event':
                    continue
                query = Q(pk__in=[])
                scoped_fields = []
                for field in model._meta.fields:
                    if not field.is_relation:
                        continue
                    related = field.related_model._meta.label_lower
                    if related in records and related not in SHARED:
                        ids = list(records[related])
                        query |= Q(**{field.attname + '__in': ids})
                        scoped_fields.append((field, ids))
                candidates = model.objects.filter(query)
                for field in model._meta.fields:
                    if field.is_relation and field.related_model._meta.label_lower == 'events.event':
                        candidates = candidates.filter(Q(**{field.attname: event.pk}) | Q(**{field.attname + '__isnull': True}))
                    elif field.is_relation and field.related_model._meta.label_lower == 'participants.eventparticipant':
                        candidates = candidates.filter(Q(**{field.name + '__event_id': event.pk}) | Q(**{field.attname + '__isnull': True}))
                for field, ids in scoped_fields:
                    candidates = candidates.filter(Q(**{field.attname + '__in': ids}) | Q(**{field.attname + '__isnull': True}))
                for obj in candidates:
                    bucket = records.setdefault(label, {})
                    if obj.pk not in bucket:
                        bucket[obj.pk] = obj
                        changed = True
            if not changed:
                break
        # Include audit by explicit event context OR scoped object identity for
        # legacy records without an event key. An explicit other event wins.
        Audit = apps.get_model('audit', 'AuditLog')
        query = Q(details__event=str(event.pk))
        for label, bucket in records.items():
            query |= Q(object_label__iexact=label, object_id__in=list(bucket)) & ~Q(details__has_key='event')
        records['audit.auditlog'] = {o.pk: o for o in Audit.objects.filter(query)}
        # Apply selected modules, always retain event/team/audit and profiles for
        # identifiers. Dependency closure below retains FK targets as needed.
        selected = {label: bucket for label, bucket in records.items()
            if label.startswith('events.') or label in ['audit.auditlog', 'retention.legalhold'] or model_module(apps.get_model(label)) in modules}
        omissions = {label: len(bucket) for label, bucket in records.items() if label not in selected and bucket}
        for _ in range(len(models) + 1):
            changed = False
            for label, bucket in list(selected.items()):
                model = apps.get_model(label)
                for field in model._meta.fields:
                    if not field.is_relation or field.related_model._meta.label_lower in EXCLUDED:
                        continue
                    related = field.related_model._meta.label_lower
                    ids = {getattr(o, field.attname) for o in bucket.values()} - {None}
                    if related not in SHARED:
                        # Domain FK targets must have been proven event-owned.
                        allowed = records.get(related, {})
                        objects = [allowed[pk] for pk in ids if pk in allowed]
                    else:
                        objects = list(field.related_model.objects.filter(pk__in=ids))
                    target = selected.setdefault(related, {})
                    for obj in objects:
                        if obj.pk not in target:
                            target[obj.pk] = obj
                            changed = True
            if not changed:
                break
        Topic = apps.get_model('profiles', 'ProfileTopic')
        rules = event.settings.get('participant_topics')
        topics = Topic.objects.all() if rules is None else Topic.objects.filter(pk__in=[r['topic'] for r in rules if r.get('enabled')])
        selected['profiles.profiletopic'] = {o.pk: o for o in topics}
        data, schemas, media, missing = {}, {}, {}, []
        for label, bucket in sorted(selected.items()):
            model = apps.get_model(label)
            fields = [f for f in model._meta.fields if f.name not in ['password', 'last_login', 'groups', 'user_permissions']]
            schemas[label] = {'table': model._meta.db_table, 'columns': {f.attname: f.db_type(connection) for f in fields},
                'relations': {f.attname: f.related_model._meta.label_lower for f in fields if f.is_relation}}
            data[label] = []
            for obj in sorted(bucket.values(), key=lambda o: str(o.pk)):
                row = {f.attname: getattr(obj, f.attname) for f in fields}
                if label == 'organizations.organization':
                    row['onboarding_draft'] = {k: row['onboarding_draft'][k] for k in ['organization', 'contact', 'email', 'phone', 'contact_role', 'notes', 'description'] if k in row['onboarding_draft']}
                # No dangling IDs into another event or omitted global data.
                for field in fields:
                    if field.is_relation and row[field.attname] not in selected.get(field.related_model._meta.label_lower, {}):
                        row[field.attname] = None
                data[label].append(row)
                key = row.get('storage_key')
                if key and not row.get('removed_at'):
                    target = 'media/' + hashlib.sha256(str(key).encode()).hexdigest() + Path(key).suffix.lower()[:12]
                    try:
                        destination = directory / target
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        with default_storage.open(key, 'rb') as source, destination.open('wb') as output:
                            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                                output.write(chunk)
                        media[str(key)] = target
                    except (FileNotFoundError, SuspiciousFileOperation):
                        missing.append({'model': label, 'id': str(obj.pk), 'reason': 'Arquivo não disponível no armazenamento'})
        return json.loads(dump({'event': str(event.pk), 'records': data, 'schemas': schemas, 'media': media,
            'missingMedia': missing, 'omittedModules': {label: count for label, count in omissions.items() if label not in selected}, 'snapshotMode': 'repeatable-read', 'capturedAt': captured_at}))


def sql_snapshot(snapshot):
    """Isolated PostgreSQL schema, native columns, explicit relation metadata.

    Never replay against the production schema; omitted FK targets are nullable.
    """
    quote = connection.ops.quote_name
    lines = ['BEGIN;', 'SET LOCAL standard_conforming_strings = on;', 'CREATE SCHEMA IF NOT EXISTS event_export;', 'SET LOCAL search_path TO event_export;',
        '-- Isolated event snapshot; no credentials, triggers or production mutations.']
    for label, schema in snapshot['schemas'].items():
        table = quote(schema['table'])
        columns = ', '.join(f'{quote(name)} {kind}' + (' PRIMARY KEY' if name == 'id' else '') for name, kind in schema['columns'].items())
        lines.append(f'CREATE TABLE {table} ({columns});')
        for row in snapshot['records'][label]:
            values = []
            for name, kind in schema['columns'].items():
                value = row.get(name)
                if value is None:
                    values.append('NULL')
                elif kind == 'jsonb':
                    values.append("'" + dump(value).replace("'", "''") + "'::jsonb")
                elif isinstance(value, bool):
                    values.append('TRUE' if value else 'FALSE')
                else:
                    values.append("'" + str(value).replace("'", "''") + "'")
            names = ', '.join(quote(name) for name in schema['columns'])
            lines.append(f'INSERT INTO {table} ({names}) VALUES ({", ".join(values)});')
    for label, schema in snapshot['schemas'].items():
        for name, related in schema['relations'].items():
            if related in snapshot['schemas']:
                lines.append(f'ALTER TABLE {quote(schema["table"])} ADD FOREIGN KEY ({quote(name)}) REFERENCES {quote(snapshot["schemas"][related]["table"])} (id) DEFERRABLE INITIALLY DEFERRED;')
    lines.append('COMMIT;')
    return '\n'.join(lines)
