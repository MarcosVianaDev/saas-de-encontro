from rest_framework.exceptions import ValidationError
from .models import ProfileTopic


def event_topics(event):
    configured = event.settings.get('participant_topics')
    topics = ProfileTopic.objects.order_by('created_at')
    if configured is None:
        return [(topic, {'required': False, 'minimum': 1}) for topic in topics]
    rules = {item['topic']: item for item in configured if item.get('enabled')}
    return [(topic, rules[str(topic.pk)]) for topic in topics if str(topic.pk) in rules]


def topic_payload(topics):
    return [{'id': str(topic.pk), 'key': topic.key, 'name': topic.name,
             'options': topic.options, 'multiple': topic.multiple, 'showInFilter': topic.show_in_filter,
             'filterMultiple': topic.filter_multiple,
             'required': rule.get('required', False), 'minimum': rule.get('minimum', 1)}
            for topic, rule in topics]


def available_filter_topics(event, topics=None):
    return {topic.key: topic for topic, _ in (event_topics(event) if topics is None else topics)
            if topic.show_in_filter}


def selected_topic_filters(filters, topics):
    """Ignore stored preferences for hidden/disabled topics and removed choices."""
    selected = filters.get('topics', {})
    result = {}
    for key, topic in topics.items():
        # Interests were already a discovery filter before dynamic topics.
        # Legacy purpose was only a preference; do not activate it implicitly.
        values = selected.get(key, filters.get('interests', []) if key == 'interests' else [])
        values = list(dict.fromkeys(value for value in values if value in topic.options))
        if not topic.filter_multiple:
            values = values[:1]
        if values:
            result[key] = values
    return result


def normalized_topic_filters(filters, topics):
    selected = selected_topic_filters(filters, topics)
    return {**filters, 'topics': selected, 'interests': selected.get('interests', [])}


def validate_topic_requirements(event, answers):
    for topic, rule in event_topics(event):
        selected = list(dict.fromkeys(answers.get(topic.key, [])))
        selected = [value for value in selected if value in topic.options]
        if not topic.multiple and len(selected) > 1:
            raise ValidationError(f'{topic.name}: selecione apenas uma opção.')
        minimum = rule.get('minimum', 1) if rule.get('required') else 0
        if len(selected) < minimum:
            raise ValidationError(f'{topic.name}: selecione pelo menos {minimum} opção(ões).')
