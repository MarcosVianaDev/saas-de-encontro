from django.db import migrations, models


def initialize_existing_filters(apps, schema_editor):
    Topic = apps.get_model('profiles', 'ProfileTopic')
    topics = Topic.objects.using(schema_editor.connection.alias)
    topics.filter(key__in=['interests', 'purpose']).update(show_in_filter=True)
    topics.update(filter_multiple=models.F('multiple'))


def seed_filter_topics(apps, schema_editor):
    Topic = apps.get_model('profiles', 'ProfileTopic')
    topics = Topic.objects.using(schema_editor.connection.alias)
    topics.get_or_create(key='orientation', defaults={
        'name': 'Orientação',
        'options': ['Heterossexual', 'Homossexual', 'Bissexual'],
        'multiple': False,
        'show_in_filter': True,
        'filter_multiple': False,
    })


class Migration(migrations.Migration):
    dependencies = [('profiles', '0009_participantprofile_height_cm')]
    operations = [
        migrations.AddField(
            model_name='profiletopic', name='show_in_filter',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profiletopic', name='filter_multiple',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(initialize_existing_filters, migrations.RunPython.noop),
        migrations.RunPython(seed_filter_topics, migrations.RunPython.noop),
    ]
