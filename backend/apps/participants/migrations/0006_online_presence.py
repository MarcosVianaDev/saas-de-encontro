from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('participants', '0005_existing_activation')]

    operations = [
        migrations.AlterField(
            model_name='eventparticipant',
            name='presence',
            field=models.CharField(max_length=12, default='UNKNOWN', choices=[
                ('UNKNOWN', 'Não confirmada'), ('PRESENT', 'Presente'),
                ('ABSENT', 'Ausente'), ('OUTSIDE', 'Temporariamente fora'),
                ('DISTANT', 'Fora do limite'),
            ]),
        ),
    ]
