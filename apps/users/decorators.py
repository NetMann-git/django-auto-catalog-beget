from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """
    Разрешает доступ только пользователям с указанными ролями.

    Пример:

    @role_required("manager", "admin")
    """

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            profile = getattr(request.user, "profile", None)

            if profile is None:
                messages.error(request, "Профиль пользователя не найден.")
                return redirect("users:dashboard")

            if profile.role not in allowed_roles:
                messages.error(
                    request,
                    "У вас нет доступа к этой странице."
                )
                return redirect("users:dashboard")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator