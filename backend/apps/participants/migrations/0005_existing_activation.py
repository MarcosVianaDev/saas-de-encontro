from django.db import migrations
from django.db.models import F

def forwards(apps,schema_editor):
    Participant=apps.get_model('participants','EventParticipant')
    Participant.objects.filter(is_active=True,activated_at__isnull=True).update(activated_at=F('created_at'),onboarding_completed_at=F('created_at'),registration_status='ACTIVE')

class Migration(migrations.Migration):
    dependencies=[('participants','0004_eventparticipant_location_exception_until_and_more')]
    operations=[migrations.RunPython(forwards,migrations.RunPython.noop)]
