"""Admin vs Employee role helpers.

Week 1 stores roles as Django Groups named "Admin" and "Employee".
The Employee model (with its own role field) comes in Week 2.
"""

ADMIN_GROUP = "Admin"
EMPLOYEE_GROUP = "Employee"


def is_admin(user):
    """True if the user is a superuser or belongs to the Admin group."""
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=ADMIN_GROUP).exists()


def is_employee(user):
    """True if the user belongs to the Employee group."""
    if not getattr(user, "is_authenticated", False):
        return False
    return user.groups.filter(name=EMPLOYEE_GROUP).exists()


def get_role_label(user):
    if not getattr(user, "is_authenticated", False):
        return ""
    if is_admin(user):
        return "Admin"
    if is_employee(user):
        return "Employee"
    return "User"
