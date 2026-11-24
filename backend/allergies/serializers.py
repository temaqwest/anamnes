from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Allergy


class AllergySerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergy
        fields = ("id", "name")

    def validate_name(self, name):
        return " ".join(name.split())

    def create(self, validated_data):
        name_key = validated_data["name"].casefold()
        try:
            with transaction.atomic():
                return Allergy.objects.create(name_key=name_key, **validated_data)
        except IntegrityError:
            if Allergy.objects.filter(owner=validated_data["owner"], name_key=name_key).exists():
                raise serializers.ValidationError({"name": "Этот аллерген уже есть в списке."}) from None
            raise
