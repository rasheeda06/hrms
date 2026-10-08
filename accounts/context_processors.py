"""Make the current user's role available in every template."""

from accounts.roles import get_role_label, is_admin, is_employee


def roles(request):
    return {
        "user_is_admin": is_admin(request.user),
        "user_is_employee": is_employee(request.user),
        "user_role_label": get_role_label(request.user),
    }
