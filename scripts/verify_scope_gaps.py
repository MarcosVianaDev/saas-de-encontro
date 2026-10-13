from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.organizations.models import Organization
from apps.events.models import Event
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile, ProfileField, ParticipantFieldValue
from apps.matches.models import Match
from apps.messaging.models import Conversation, Message
from apps.passes.models import PassType, EventPassOffer, ParticipantPass, PassUsage


def verify(label, instance):
    try:
        instance.full_clean()
        print(label + ': aceito por full_clean')
    except ValidationError as exc:
        print(label + ': rejeitado: ' + str(exc))


with transaction.atomic():
    organization = Organization.objects.create(name='Verificacao temporaria')
    event = Event.objects.create(organization=organization, name='A')
    other_event = Event.objects.create(organization=organization, name='B')
    participants = []
    import uuid
    for index in range(4):
        user = get_user_model().objects.create_user(username='scope-check-' + uuid.uuid4().hex)
        participants.append(EventParticipant.objects.create(user=user, event=other_event if index == 3 else event))
    first, second, outsider, other = participants
    first, second = sorted((first, second), key=lambda participant: participant.pk)
    first.is_active = True
    verify('Participante ativo sem perfil/fotos', first)
    verify('Perfil sem nascimento/genero/bio', ParticipantProfile(participant=first, first_name='A', last_name='B'))
    match = Match(participant=first, partner=second)
    verify('Match sem likes reciprocos', match)
    match.save()
    conversation = Conversation.objects.create(match=match)
    verify('Mensagem enviada por terceiro', Message(conversation=conversation, sender=outsider, body='teste'))
    match.is_active = False
    match.save()
    verify('Mensagem em match encerrado', Message(conversation=conversation, sender=first, body='teste'))
    pass_type = PassType.objects.create(name='Passe')
    offer = EventPassOffer.objects.create(event=event, pass_type=pass_type, price=0)
    participant_pass = ParticipantPass.objects.create(participant=first, offer=offer)
    verify('Uso de passe para participante de outro evento', PassUsage(participant_pass=participant_pass, revealed_participant=other))
    field = ProfileField.objects.create(name='Campo global')
    verify('Valor de campo global em participante', ParticipantFieldValue(participant=first, field=field, value={'text': 'valor'}))
    transaction.set_rollback(True)
print('Todos os registros temporarios foram revertidos.')
