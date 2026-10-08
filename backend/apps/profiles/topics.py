from rest_framework.exceptions import ValidationError
from .models import ProfileTopic


def event_topics(event):
    configured = event.settings.get('participant_topics')
    topics = ProfileTopic.objects.order_by('created_at')
    if configured is None:
        return [(topic, {'required': False, 'minimum': 1}) for topic in topics]
    rules = {item['topic']: item for item in configured if item.get('enabled')}
    return [(topic, rules[str(topic.pk)]) for topic in topics if str(topic.pk) in rules]


def validate_topic_requirements(event, answers):
    for topic, rule in event_topics(event):
        selected = list(dict.fromkeys(answers.get(topic.key, [])))
        selected = [value for value in selected if value in topic.options]
        if not topic.multiple and len(selected) > 1:
            raise ValidationError(f'{topic.name}: selecione apenas uma opção.')
        minimum = rule.get('minimum', 1) if rule.get('required') else 0
        if len(selected) < minimum:
            raise ValidationError(f'{topic.name}: selecione pelo menos {minimum} opção(ões).')
