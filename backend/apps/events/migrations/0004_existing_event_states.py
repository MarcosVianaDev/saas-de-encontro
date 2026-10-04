from django.db import migrations
from django.utils import timezone


def forwards(apps, schema_editor):
    Event = apps.get_model('events', 'Event')
    now = timezone.now()
    for event in Event.objects.all():
        if event.ends_at and event.ends_at <= now:
            Event.objects.filter(pk=event.pk).update(state='CLOSED', closed_at=event.ends_at)
        elif event.starts_at and event.starts_at <= now:
            Event.objects.filter(pk=event.pk).update(state='RUNNING', opened_at=event.starts_at, opening_origin='manual')
        elif event.starts_at:
            Event.objects.filter(pk=event.pk).update(state='SCHEDULED')


class Migration(migrations.Migration):
    dependencies = [('events', '0003_event_archived_at_event_closed_at_event_latitude_and_more')]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
