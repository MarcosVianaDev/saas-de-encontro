from django.utils import timezone
from rest_framework import serializers
from apps.profiles.models import ProfileTopic
from apps.profiles.constants import BIO_MIN_LENGTH, BIO_MAX_LENGTH
from apps.profiles.locations import BRAZIL_STATES
from apps.profiles.topics import available_filter_topics


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, max_length=200)


class ProfileSerializer(serializers.Serializer):
    first = serializers.CharField(max_length=150)
    last = serializers.CharField(max_length=150)
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=1900)
    gender = serializers.ChoiceField(choices=["Mulheres", "Homens", "Não binário", "Prefiro não informar"])
    bio = serializers.CharField(min_length=BIO_MIN_LENGTH, max_length=BIO_MAX_LENGTH)
    residenceState = serializers.ChoiceField(choices=BRAZIL_STATES, required=False, allow_blank=True)
    height = serializers.IntegerField(min_value=50, max_value=250, required=False, allow_null=True)
    interests = serializers.ListField(child=serializers.CharField(max_length=200), required=False)
    purpose = serializers.CharField(max_length=200, allow_blank=True, required=False)
    topicAnswers = serializers.DictField(child=serializers.ListField(child=serializers.CharField(max_length=200)), required=False)

    def validate_interests(self, values):
        topic = ProfileTopic.objects.filter(key='interests').first()
        if not topic or any(value not in topic.options for value in values) or (not topic.multiple and len(values) > 1):
            raise serializers.ValidationError('Selecione apenas opções cadastradas e respeite a escolha única do tópico.')
        return list(dict.fromkeys(values))

    def validate_purpose(self, value):
        topic = ProfileTopic.objects.filter(key='purpose').first()
        if value and (not topic or value not in topic.options):
            raise serializers.ValidationError('Selecione uma opção cadastrada para este tópico.')
        return value

    def validate_topicAnswers(self, answers):
        topics = {topic.key: topic for topic in ProfileTopic.objects.all()}
        for key, values in answers.items():
            topic = topics.get(key)
            if not topic or any(value not in topic.options for value in values) or (not topic.multiple and len(values) > 1):
                raise serializers.ValidationError('Selecione apenas opções cadastradas e respeite a escolha única do tópico.')
            answers[key] = list(dict.fromkeys(values))
        return answers

    def validate(self, data):
        today = timezone.localdate()
        if (data["year"], data["month"]) > (today.year, today.month):
            raise serializers.ValidationError("Nascimento não pode estar no futuro.")
        return data


class FilterSerializer(serializers.Serializer):
    topics = serializers.DictField(child=serializers.ListField(
        child=serializers.CharField(max_length=200), max_length=100), required=False, default=dict)
    minHeight = serializers.IntegerField(min_value=50, max_value=250, required=False, allow_null=True, default=None)
    maxHeight = serializers.IntegerField(min_value=50, max_value=250, required=False, allow_null=True, default=None)
    min = serializers.IntegerField(min_value=18, max_value=70)
    max = serializers.IntegerField(min_value=18, max_value=100)
    gender = serializers.ChoiceField(choices=["Todos", "Mulheres", "Homens"])
    interests = serializers.ListField(child=serializers.CharField(max_length=200))
    purpose = serializers.CharField(max_length=200, allow_blank=True)

    def validate_topics(self, values):
        event = self.context['event']
        available = available_filter_topics(event)
        for key, options in values.items():
            if key not in available or any(option not in available[key].options for option in options):
                raise serializers.ValidationError('Selecione opções de tópicos habilitados para o filtro deste evento.')
            if not available[key].filter_multiple and len(set(options)) > 1:
                raise serializers.ValidationError(f'{available[key].name}: selecione apenas uma opção no filtro.')
        return {key: list(dict.fromkeys(options)) for key, options in values.items()}

    def validate_interests(self, values):
        topic = ProfileTopic.objects.filter(key='interests').first()
        if any(value not in (topic.options if topic else []) for value in values):
            raise serializers.ValidationError('Selecione apenas opções cadastradas e respeite a escolha única do tópico.')
        if topic and topic.show_in_filter and not topic.filter_multiple and len(set(values)) > 1:
            raise serializers.ValidationError('Selecione apenas uma opção no filtro de interesses.')
        return values

    def validate_purpose(self, value):
        topic = ProfileTopic.objects.filter(key='purpose').first()
        if value and value not in (topic.options if topic else []):
            raise serializers.ValidationError('Selecione uma opção cadastrada para este tópico.')
        return value

    def validate(self, data):
        if data["min"] > data["max"]:
            raise serializers.ValidationError("A idade mínima não pode superar a máxima.")
        if data.get('minHeight') is not None and data.get('maxHeight') is not None and data['minHeight'] > data['maxHeight']:
            raise serializers.ValidationError('A altura mínima não pode superar a máxima.')
        return data


class DecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["LIKE", "PASS"])


class MessageSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=2000)


class PhotoDeleteSerializer(serializers.Serializer):
    url = serializers.CharField(max_length=1024)
