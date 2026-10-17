import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('passes', '0005_participantpass_participant_initial_gift_unique')]

    operations = [
        migrations.CreateModel(
            name='InitialGiftSweep',
            fields=[
                ('id', models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ('token', models.UUIDField(editable=False, null=True)),
                ('cursor', models.UUIDField(editable=False, null=True)),
                ('expires_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
