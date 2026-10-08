from django.db import migrations


def seed_topics(apps, schema_editor):
    Topic = apps.get_model('profiles', 'ProfileTopic')
    Profile = apps.get_model('profiles', 'ParticipantProfile')
    database = schema_editor.connection.alias
    interests = ['Música', 'Viagens', 'Tecnologia', 'Gastronomia', 'Esportes', 'Arte', 'Networking']
    purposes = ['Networking', 'Amizade', 'Relacionamento', 'Negócios', 'Troca de ideias']
    for key, name, options, multiple in [
        ('interests', 'Interesses', interests, True),
        ('purpose', 'Finalidade no evento', purposes, False),
    ]:
        Topic.objects.using(database).get_or_create(key=key, defaults={'name': name, 'options': options, 'multiple': multiple})
    for profile in Profile.objects.using(database).iterator():
        profile.topic_answers = {
            **profile.topic_answers,
            'interests': [value for value in profile.interests if value in interests],
            'purpose': [profile.purpose] if profile.purpose in purposes else [],
        }
        profile.interests = profile.topic_answers['interests']
        profile.purpose = next(iter(profile.topic_answers['purpose']), '')
        profile.save(using=database, update_fields=['topic_answers', 'interests', 'purpose'])


class Migration(migrations.Migration):
    dependencies = [('profiles', '0005_profiletopic_participantprofile_topic_answers_and_more')]
    operations = [migrations.RunPython(seed_topics, migrations.RunPython.noop)]
