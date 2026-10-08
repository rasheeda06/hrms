"""View decorators that enforce HRMS roles."""

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render

from accounts.roles import is_admin


def admin_required(view):
    """Allow only Admin-role users. Everyone else gets login or 403."""

    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not is_admin(request.user):
            return render(request, "403.html", status=403)
        return view(request, *args, **kwargs)

    return _wrapped
