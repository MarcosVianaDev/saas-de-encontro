from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('messaging', '0002_message_read_at')]

    operations = [migrations.AddIndex(
        model_name='message',
        index=models.Index(fields=['conversation', 'updated_at', 'id'], name='message_conversation_sync_idx'),
    ), migrations.AddIndex(
        model_name='message',
        index=models.Index(fields=['conversation'], condition=models.Q(read_at__isnull=True), name='message_unread_sync_idx'),
    )]
