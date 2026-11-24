from datetime import UTC, datetime, timedelta
from io import StringIO
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from .models import AccountEmail, RegistrationInvite


@override_settings(
    ANAMNES_SIGNUP_ENABLED=True,
    ANAMNES_PUBLIC_URL="https://archive.example.test",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class AccountTests(TestCase):
    email = "patient@example.test"
    password = "Invite-Maple!40922"

    def post(self, action, payload, *, client=None):
        return (client or self.client).post(f"/api/auth/{action}/", payload, content_type="application/json")

    def invite(self, email=None):
        output = StringIO()
        call_command("create_invite", email or self.email, stdout=output)
        link = urlsplit(output.getvalue().strip())
        self.assertEqual((link.scheme, link.netloc, link.path), ("https", "archive.example.test", "/register"))
        return parse_qs(link.fragment)["invite"][0]

    def link_from_mail(self, path):
        url = urlsplit(next(line for line in mail.outbox[-1].body.splitlines() if line.startswith("https://")))
        self.assertEqual((url.scheme, url.netloc, url.path, url.query), ("https", "archive.example.test", path, ""))
        return {name: values[0] for name, values in parse_qs(url.fragment).items()}

    def register(self, *, invite=None, email=None):
        return self.post("register", {
            "email": email or self.email, "password": self.password, "invite": invite or self.invite(),
        })

    def test_invitation_is_bound_to_email_and_required(self):
        self.assertEqual(self.register(invite="invalid").status_code, 400)
        token = self.invite()
        self.assertEqual(self.register(invite=token, email="other@example.test").status_code, 400)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(self.register(invite=token, email=self.email.upper()).status_code, 201)
        self.assertEqual(self.register(invite=token).status_code, 400)
        user = get_user_model().objects.get()
        self.assertFalse(user.is_active or user.is_staff or user.is_superuser)
        self.assertTrue(user.check_password(self.password))
        self.assertEqual(mail.outbox[0].to, [self.email])

    def test_email_has_to_be_confirmed_before_access_to_archive(self):
        self.assertEqual(self.register().status_code, 201)
        credentials = {"username": self.email, "password": self.password}
        self.assertEqual(self.post("login", credentials).status_code, 401)
        self.assertEqual(self.client.get("/api/documents/").status_code, 403)
        payload = self.link_from_mail("/confirm-email")
        self.assertEqual(self.post("verify-email", {**payload, "token": "invalid"}).status_code, 400)
        self.assertEqual(self.post("verify-email", payload).status_code, 200)
        self.assertEqual(self.post("verify-email", payload).status_code, 400)
        self.assertEqual(self.post("login", credentials).json(), {"username": self.email})
        self.assertEqual(self.client.get("/api/auth/session/").json(), {"username": self.email})
        self.assertEqual(self.client.get("/api/documents/").json(), [])
        self.assertGreater(len(self.client.get("/api/areas/").json()), 0)

    def test_invitation_and_email_confirmation_expire(self):
        old_invite = self.invite()
        stored = RegistrationInvite.objects.get()
        self.assertNotEqual(stored.token_hash, old_invite)
        RegistrationInvite.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.register(invite=old_invite).status_code, 400)

        created_at = datetime(2026, 11, 24, 12)
        with patch("accounts.services.verification_token._now", return_value=created_at):
            self.assertEqual(self.register().status_code, 201)
        payload = self.link_from_mail("/confirm-email")
        with patch("accounts.services.verification_token._now", return_value=created_at + timedelta(hours=2)):
            self.assertEqual(self.post("verify-email", payload).status_code, 400)

    def test_existing_email_shaped_username_cannot_be_shadowed_by_registration(self):
        token = self.invite()
        username = self.email.upper()
        get_user_model().objects.create_user(username=username, password=self.password)
        with self.assertRaises(CommandError):
            self.invite()
        self.assertEqual(self.register(invite=token).status_code, 400)
        self.assertEqual(self.post("login", {"username": username, "password": self.password}).json(),
                         {"username": username})

    def test_an_exact_legacy_username_takes_precedence_over_a_normalized_email(self):
        username = "straße@example.test"
        address = "strasse@example.test"
        users = get_user_model().objects
        users.create_user(username=username, password=self.password)
        other_password = "Cedar-Other!62710"
        account = users.create_user(username="internal-account", email=address, password=other_password)
        AccountEmail.objects.create(user=account, address=address, verified_at=timezone.now())

        self.assertEqual(self.post("login", {"username": username, "password": self.password}).json(),
                         {"username": username})
        self.assertEqual(self.post("login", {"username": username, "password": other_password}).status_code, 401)
        self.assertEqual(self.post("login", {"username": address.upper(), "password": other_password}).json(),
                         {"username": address})

    def test_resend_and_recovery_have_generic_responses(self):
        self.assertEqual(self.register().status_code, 201)
        known = self.post("resend-verification", {"email": self.email})
        missing = self.post("resend-verification", {"email": "missing@example.test"})
        self.assertEqual((known.status_code, known.json()), (missing.status_code, missing.json()))
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(self.post("verify-email", self.link_from_mail("/confirm-email")).status_code, 200)

        known = self.post("password-reset", {"email": self.email})
        missing = self.post("password-reset", {"email": "missing@example.test"})
        self.assertEqual((known.status_code, known.json()), (missing.status_code, missing.json()))
        self.assertEqual(len(mail.outbox), 3)

    def test_reset_link_works_once_and_invalidates_the_old_session(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.post("verify-email", self.link_from_mail("/confirm-email")).status_code, 200)
        self.assertEqual(self.post("login", {"username": self.email, "password": self.password}).status_code, 200)
        self.assertEqual(self.post("password-reset", {"email": self.email}).status_code, 200)
        new_password = "Cedar-Reset!62710"
        payload = {**self.link_from_mail("/reset-password"), "password": new_password}
        self.assertEqual(self.post("password-reset/confirm", payload).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/session/").json(), {"username": None})
        self.assertEqual(self.post("password-reset/confirm", payload).status_code, 400)
        self.assertEqual(self.post("login", {"username": self.email, "password": self.password}).status_code, 401)
        self.assertEqual(self.post("login", {"username": self.email.upper(), "password": new_password}).status_code, 200)

    def test_anonymous_account_actions_require_csrf(self):
        browser = Client(enforce_csrf_checks=True)
        browser.get("/api/auth/session/")
        for action in ("register", "verify-email", "resend-verification", "password-reset", "password-reset/confirm"):
            with self.subTest(action=action):
                self.assertEqual(self.post(action, {}, client=browser).status_code, 403)

    @patch("accounts.security.timezone.now", return_value=datetime(2026, 11, 24, 12, tzinfo=UTC))
    def test_login_attempts_are_limited_per_identifier_and_email_resend_is_bounded(self, _now):
        self.assertEqual(self.register().status_code, 201)
        for _ in range(6):
            self.assertEqual(self.post("resend-verification", {"email": self.email}).status_code, 200)
        self.assertEqual(len(mail.outbox), 5)

        for _ in range(12):
            self.assertEqual(self.post("login", {"username": self.email, "password": "invalid"}).status_code, 401)
        result = self.post("login", {"username": self.email.upper(), "password": "invalid"})
        self.assertEqual(result.status_code, 429)
        self.assertEqual(result["Retry-After"], "600")

    @override_settings(ANAMNES_SIGNUP_ENABLED=False)
    def test_registration_can_be_paused_without_breaking_existing_login(self):
        user = get_user_model().objects.create_user(username="existing-local", password=self.password)
        self.assertEqual(self.register(invite="invalid").status_code, 403)
        self.assertEqual(self.post("login", {"username": user.username, "password": self.password}).json(),
                         {"username": "existing-local"})
