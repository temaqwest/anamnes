from django.conf import settings
from django.db import models


class AccountEmail(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account_email")
    address = models.EmailField(unique=True)
    verified_at = models.DateTimeField(null=True, blank=True)


class RegistrationInvite(models.Model):
    token_hash = models.CharField(max_length=64, primary_key=True)
    address = models.EmailField()
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)


class AuthThrottle(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    expires_at = models.DateTimeField(db_index=True)
    hits = models.PositiveIntegerField(default=0)
