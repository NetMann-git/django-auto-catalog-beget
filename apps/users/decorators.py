from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """
    Доступ только пользователям с указанными ролями.
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("users:login")

            profile = getattr(request.user, "profile", None)

            if profile is None:
                messages.error(request, "Профиль пользователя не найден.")
                return redirect("users:dashboard")

            if profile.role not in allowed_roles:
                messages.error(request, "У вас нет доступа к этой странице.")
                return redirect("users:dashboard")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator