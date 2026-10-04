from django.db import migrations

def forwards(apps,schema_editor):
    Pass=apps.get_model('passes','ParticipantPass')
    for p in Pass.objects.select_related('offer__pass_type'):
        Pass.objects.filter(pk=p.pk).update(reveal_limit=p.offer.pass_type.reveal_limit,sale_amount=p.offer.price,origin='Histórico anterior à operação MVP')

class Migration(migrations.Migration):
    dependencies=[('passes','0002_participantpass_expiry_notified_at_and_more')]
    operations=[migrations.RunPython(forwards,migrations.RunPython.noop)]
