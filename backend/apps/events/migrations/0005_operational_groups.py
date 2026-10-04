from django.db import migrations


def groups(apps,schema_editor):
    Group=apps.get_model('auth','Group')
    for name in ['Moderador','Operador']:
        Group.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies=[('events','0004_existing_event_states'),('auth','0012_alter_user_first_name_max_length')]
    operations=[migrations.RunPython(groups,migrations.RunPython.noop)]
