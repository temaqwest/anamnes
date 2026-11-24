from datetime import datetime, timezone as utc

from django.db.models import F
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import AuthThrottle


WINDOW_SECONDS = 600


def allow_attempt(action, kind, value, limit):
    now = timezone.now()
    stop = (int(now.timestamp()) // WINDOW_SECONDS + 1) * WINDOW_SECONDS
    key = salted_hmac("accounts.throttle", f"{action}:{kind}:{stop}:{value}", algorithm="sha256").hexdigest()
    expires_at = datetime.fromtimestamp(stop, tz=utc.utc)
    _, created = AuthThrottle.objects.get_or_create(key=key, defaults={"expires_at": expires_at})
    if created:
        AuthThrottle.objects.filter(expires_at__lte=now).delete()
    return bool(AuthThrottle.objects.filter(key=key, hits__lt=limit).update(hits=F("hits") + 1))
