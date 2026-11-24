from django.urls import path
from django.views.decorators.cache import never_cache

from . import views


urlpatterns = [
    path("session/", never_cache(views.session)),
    path("login/", never_cache(views.SignIn.as_view())),
    path("logout/", never_cache(views.sign_out)),
    path("register/", never_cache(views.Register.as_view())),
    path("verify-email/", never_cache(views.VerifyEmail.as_view())),
    path("resend-verification/", never_cache(views.ResendVerification.as_view())),
    path("password-reset/", never_cache(views.RequestPasswordReset.as_view())),
    path("password-reset/confirm/", never_cache(views.ResetPassword.as_view())),
]
