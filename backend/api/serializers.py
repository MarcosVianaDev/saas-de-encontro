from django.utils import timezone
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, max_length=200)


class ProfileSerializer(serializers.Serializer):
    first = serializers.CharField(max_length=150)
    last = serializers.CharField(max_length=150)
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=1900)
    gender = serializers.ChoiceField(choices=["Mulheres", "Homens", "Não binário", "Prefiro não informar"])
    bio = serializers.CharField(min_length=50, max_length=200)

    def validate(self, data):
        today = timezone.localdate()
        if (data["year"], data["month"]) > (today.year, today.month):
            raise serializers.ValidationError("Nascimento não pode estar no futuro.")
        return data


class FilterSerializer(serializers.Serializer):
    min = serializers.IntegerField(min_value=18, max_value=70)
    max = serializers.IntegerField(min_value=18, max_value=100)
    gender = serializers.ChoiceField(choices=["Todos", "Mulheres", "Homens"])
    interests = serializers.ListField(child=serializers.ChoiceField(choices=["Música", "Viagens", "Tecnologia", "Gastronomia", "Esportes", "Arte", "Networking", "Outros"]), max_length=8)
    purpose = serializers.ChoiceField(choices=["Networking", "Amizade", "Relacionamento", "Negócios", "Troca de ideias", "Outros"])

    def validate(self, data):
        if data["min"] > data["max"]:
            raise serializers.ValidationError("A idade mínima não pode superar a máxima.")
        return data


class DecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["LIKE", "PASS"])


class MessageSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=2000)


class PhotoDeleteSerializer(serializers.Serializer):
    url = serializers.CharField(max_length=1024)
