from .models import Notification


def notify(participant,kind,title,body='',key=None,action_path=''):
    defaults={'participant':participant,'event':participant.event,'kind':kind,'title':title,'body':body,'action_path':action_path}
    if key: return Notification.objects.get_or_create(dedupe_key=key,defaults=defaults)[0]
    return Notification.objects.create(**defaults)
