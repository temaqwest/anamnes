import logging
from hashlib import sha256
from smtplib import SMTPException
from urllib.parse import urlencode
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import AccountEmail, RegistrationInvite


logger = logging.getLogger(__name__)
User = get_user_model()


class VerificationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "accounts.email-verification"

    def _make_hash_value(self, user, timestamp):
        return super()._make_hash_value(user, timestamp) + str(user.is_active)


verification_token = VerificationTokenGenerator()


def normalize_email(address):
    return address.strip().casefold()


def invite_hash(secret):
    return sha256(secret.encode()).hexdigest()


def address_is_taken(address):
    return (
        AccountEmail.objects.filter(address=address).exists()
        or User.objects.filter(username__iexact=address).exists()
    )


def public_link(path, **fields):
    return f"{settings.ANAMNES_PUBLIC_URL}{path}#{urlencode(fields)}"


def email_link(account, *, reset=False):
    if reset:
        title = "Сброс пароля Anamnes"
        path = "/reset-password"
        token = default_token_generator.make_token(account.user)
    else:
        title = "Подтвердите email в Anamnes"
        path = "/confirm-email"
        token = verification_token.make_token(account.user)
    link = public_link(path, uid=account.user_id, token=token)
    try:
        send_mail(
            title, f"{title}. Ссылка действует один час.\n\n{link}\n",
            None, [account.address],
        )
    except (OSError, SMTPException):
        logger.warning("Could not send an Anamnes account email.")


def register_account(address, password, invite):
    now = timezone.now()
    try:
        with transaction.atomic():
            claimed = RegistrationInvite.objects.filter(
                token_hash=invite_hash(invite), address=address, used_at__isnull=True, expires_at__gt=now,
            ).update(used_at=now)
            if not claimed or address_is_taken(address):
                return None
            user = User.objects.create_user(
                username=f"account-{uuid4().hex}", email=address, password=password, is_active=False,
            )
            return AccountEmail.objects.create(user=user, address=address)
    except IntegrityError:
        if AccountEmail.objects.filter(address=address).exists():
            return None
        raise


@transaction.atomic
def verify_email(account):
    changed = AccountEmail.objects.filter(pk=account.pk, verified_at__isnull=True).update(verified_at=timezone.now())
    if changed:
        User.objects.filter(pk=account.user_id).update(is_active=True)
    return bool(changed)
