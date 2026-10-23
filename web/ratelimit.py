"""Per-user fixed-window rate limit for costly endpoints, backed by the shared cache."""

from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render


def ai_rate_limited(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        key = f"ai-rate:{request.user.pk}"
        window = settings.AI_RATE_WINDOW_SECONDS
        cache.add(key, 0, timeout=window)
        try:
            count = cache.incr(key)
        except ValueError:  # expired between add and incr
            cache.set(key, 1, timeout=window)
            count = 1
        if count > settings.AI_RATE_LIMIT:
            return render(
                request,
                "web/partials/ai_state.html",
                {"state": "rate_limited", "window_minutes": window // 60},
                status=429,
            )
        return view(request, *args, **kwargs)

    return wrapper
