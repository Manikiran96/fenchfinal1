"""Reusable Role-Based Access Control (RBAC) helpers."""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles and not request.user.is_superuser:
                raise PermissionDenied("You do not have access to this section.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
