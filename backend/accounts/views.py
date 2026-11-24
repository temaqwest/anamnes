import json

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import AccountEmail
from .security import WINDOW_SECONDS, allow_attempt
from .serializers import (
    CredentialsSerializer, EmailSerializer, RegisterSerializer, ResetPasswordSerializer, TokenSerializer, password_errors,
)
from .services import email_link, normalize_email, register_account, verification_token, verify_email


User = get_user_model()
INVALID_LINK = "Ссылка недействительна или устарела. Запросите новую."
CONFIRMATION_SENT = "Если адрес ожидает подтверждения, мы отправим письмо со ссылкой."
RECOVERY_SENT = "Если этот адрес подтверждён в Anamnes, мы отправим ссылку для сброса пароля."


def detail(message, status=200, **kwargs):
    return JsonResponse({"detail": message}, status=status, **kwargs)


def session_data(user):
    if not user.is_authenticated:
        return {"username": None}
    email = AccountEmail.objects.filter(user=user, verified_at__isnull=False).values_list("address", flat=True).first()
    return {"username": email or user.get_username()}


@require_GET
@ensure_csrf_cookie
def session(request):
    return JsonResponse(session_data(request.user))


@require_POST
@csrf_protect
def sign_out(request):
    logout(request)
    return JsonResponse({"username": None})


@method_decorator(csrf_protect, name="dispatch")
class AccountPost(View):
    http_method_names = ["post"]
    ip_limit = 40
    identity_field = None
    identity_limit = 8
    identity_response = ""

    def post(self, request):
        action = self.__class__.__name__
        ip = request.META.get("REMOTE_ADDR", "")
        if not allow_attempt(action, "ip", ip, self.ip_limit):
            return self.throttled()
        try:
            data = json.loads(request.body)
        except (ValueError, UnicodeDecodeError):
            data = None
        if not isinstance(data, dict):
            return detail("Передайте данные в формате JSON.", 400)
        serializer = self.serializer_class(data=data)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=400)
        fields = serializer.validated_data
        if self.identity_field and not allow_attempt(
            action, "identity", fields[self.identity_field].casefold(), self.identity_limit,
        ):
            if self.identity_response:
                return detail(self.identity_response)
            return self.throttled()
        return self.perform(request, fields)

    def throttled(self):
        return detail(
            "Слишком много попыток. Попробуйте позже.", 429, headers={"Retry-After": str(WINDOW_SECONDS)},
        )


class SignIn(AccountPost):
    serializer_class = CredentialsSerializer
    ip_limit = 100
    identity_field = "username"
    identity_limit = 12

    def perform(self, request, fields):
        username = fields["username"]
        if not User.objects.filter(username=username).exists():
            email_username = AccountEmail.objects.filter(
                address=normalize_email(username), verified_at__isnull=False,
            ).values_list("user__username", flat=True).first()
            username = email_username or username
        user = authenticate(request, username=username, password=fields["password"])
        if user is None:
            return detail("Проверьте имя пользователя или email и пароль.", 401)
        login(request, user)
        return JsonResponse(session_data(user))


class Register(AccountPost):
    serializer_class = RegisterSerializer
    identity_field = "email"

    def post(self, request):
        if not settings.ANAMNES_SIGNUP_ENABLED:
            return detail("Регистрация временно закрыта.", 403)
        return super().post(request)

    def perform(self, request, fields):
        address = fields["email"]
        errors = password_errors(fields["password"], User(email=address))
        if errors:
            return JsonResponse({"password": errors}, status=400)
        account = register_account(address, fields["password"], fields["invite"])
        if account is None:
            return detail("Проверьте email и приглашение. Приглашение может быть использовано или просрочено.", 400)
        email_link(account)
        return detail("Аккаунт создан. Проверьте почту и подтвердите адрес, чтобы войти.", 201)


class VerifyEmail(AccountPost):
    serializer_class = TokenSerializer

    def perform(self, request, fields):
        account = AccountEmail.objects.select_related("user").filter(
            user_id=fields["uid"], user__is_active=False, verified_at__isnull=True,
        ).first()
        if account is None or not verification_token.check_token(account.user, fields["token"]) or not verify_email(account):
            return detail(INVALID_LINK, 400)
        return detail("Email подтверждён. Теперь можно войти в архив.")


class ResendVerification(AccountPost):
    serializer_class = EmailSerializer
    identity_field = "email"
    identity_limit = 4
    identity_response = CONFIRMATION_SENT

    def perform(self, request, fields):
        account = AccountEmail.objects.select_related("user").filter(
            address=fields["email"], user__is_active=False, verified_at__isnull=True,
        ).first()
        if account:
            email_link(account)
        return detail(CONFIRMATION_SENT)


class RequestPasswordReset(AccountPost):
    serializer_class = EmailSerializer
    identity_field = "email"
    identity_limit = 4
    identity_response = RECOVERY_SENT

    def perform(self, request, fields):
        account = AccountEmail.objects.select_related("user").filter(
            address=fields["email"], user__is_active=True, verified_at__isnull=False,
        ).first()
        if account:
            email_link(account, reset=True)
        return detail(RECOVERY_SENT)


class ResetPassword(AccountPost):
    serializer_class = ResetPasswordSerializer

    def perform(self, request, fields):
        account = AccountEmail.objects.select_related("user").filter(
            user_id=fields["uid"], user__is_active=True, verified_at__isnull=False,
        ).first()
        if account is None or not default_token_generator.check_token(account.user, fields["token"]):
            return detail(INVALID_LINK, 400)
        user = account.user
        errors = password_errors(fields["password"], user)
        if errors:
            return JsonResponse({"password": errors}, status=400)
        old_password = user.password
        user.set_password(fields["password"])
        if not User.objects.filter(pk=user.pk, password=old_password, is_active=True).update(password=user.password):
            return detail(INVALID_LINK, 400)
        return detail("Пароль изменён. Войдите с новым паролем.")
