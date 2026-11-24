from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .services import normalize_email


def password_errors(password, user):
    try:
        validate_password(password, user)
    except ValidationError as error:
        return error.messages
    return []


class CredentialsSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=254)
    password = serializers.CharField(trim_whitespace=False)


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        address = normalize_email(value)
        if len(address) > 254:
            raise serializers.ValidationError("В адресе email может быть не более 254 символов.")
        return address


class RegisterSerializer(EmailSerializer):
    password = serializers.CharField(max_length=128, trim_whitespace=False)
    invite = serializers.CharField(max_length=128)


class TokenSerializer(serializers.Serializer):
    uid = serializers.IntegerField(min_value=1, max_value=2 ** 63 - 1)
    token = serializers.CharField(max_length=128)


class ResetPasswordSerializer(TokenSerializer):
    password = serializers.CharField(max_length=128, trim_whitespace=False)
