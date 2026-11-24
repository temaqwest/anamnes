import secrets
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.utils import timezone

from accounts.models import RegistrationInvite
from accounts.services import address_is_taken, invite_hash, normalize_email, public_link


class Command(BaseCommand):
    help = "Create a single-use registration link for an email address."

    def add_arguments(self, parser):
        parser.add_argument("email")

    def handle(self, *args, **options):
        address = normalize_email(options["email"])
        try:
            validate_email(address)
        except ValidationError as error:
            raise CommandError("Specify a valid email address.") from error
        if len(address) > 254:
            raise CommandError("The email address exceeds 254 characters.")
        if address_is_taken(address):
            raise CommandError("This address already has an account or is used as a username.")
        token = secrets.token_urlsafe(32)
        RegistrationInvite.objects.create(
            token_hash=invite_hash(token), address=address, expires_at=timezone.now() + timedelta(days=7),
        )
        self.stdout.write(public_link("/register", invite=token))
