import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import transaction,connections
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.organizations.models import Organization
from apps.events.models import Event
from apps.participants.models import EventParticipant
from apps.profiles.models import ParticipantProfile
from apps.passes.models import PassType,EventPassOffer,ParticipantPass,PassUsage
from apps.passes.services import reveal
from apps.interactions.models import Interaction
from apps.audit.services import record

with transaction.atomic():
    owner=get_user_model().objects.filter(is_superuser=True,is_active=True).first()
    tag=uuid.uuid4().hex
    organization=Organization.objects.create(name='Validacao ficticia de concorrencia')
    event=Event.objects.create(organization=organization,name='Validacao ficticia: um credito, duas requisicoes',state='RUNNING',starts_at=timezone.now(),ends_at=timezone.now()+timedelta(hours=1))
    people=[]
    for i in range(3):
        user=get_user_model().objects.create_user(username=f'concurrency-{tag}-{i}',email=f'concurrency-{tag}-{i}@example.invalid')
        p=EventParticipant.objects.create(event=event,user=user,is_active=True,registration_status='ACTIVE')
        ParticipantProfile.objects.create(participant=p,first_name=f'Pessoa ficticia {i}')
        people.append(p)
    actor=people[0]
    for peer in people[1:]:Interaction.objects.create(participant=peer,target=actor,decision='LIKE')
    offer=EventPassOffer.objects.create(event=event,pass_type=PassType.objects.create(name='Um credito ficticio',reveal_limit=1),price=0)
    entitlement=ParticipantPass.objects.create(participant=actor,offer=offer,reveal_limit=1,sale_amount=0,granted_by=owner,origin='validacao de concorrencia')
    record(owner,'validation.concurrency_fixture',event,event)

barrier=Barrier(2)
def attempt():
    try:
        p=EventParticipant.objects.get(pk=actor.pk)
        barrier.wait(timeout=10)
        try:
            reveal(p,Interaction.objects.filter(target=p,decision='LIKE').select_related('participant').order_by('created_at','id'))
            return 'revealed'
        except ValidationError:return 'no-credit'
    finally:connections.close_all()

with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(lambda _:attempt(),range(2)))
assert sorted(results)==['no-credit','revealed'],results
assert PassUsage.objects.filter(participant_pass=entitlement).count()==1
assert str(entitlement.usages.get().revealed_participant_id)==str(people[1].pk)
print('PASS: two concurrent PostgreSQL connections consumed exactly one credit and revealed the oldest hidden like.')
