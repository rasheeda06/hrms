from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from accounts.roles import ADMIN_GROUP, EMPLOYEE_GROUP

DEMO_USERS = (
    {
        "username": "admin",
        "password": "AdminPass123!",
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "group": ADMIN_GROUP,
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "username": "employee",
        "password": "EmployeePass123!",
        "email": "employee@example.com",
        "first_name": "Demo",
        "last_name": "Employee",
        "group": EMPLOYEE_GROUP,
        "is_staff": False,
        "is_superuser": False,
    },
)


class Command(BaseCommand):
    help = "Create Admin and Employee groups plus two demo login accounts."

    def handle(self, *args, **options):
        groups = {}
        for name in (ADMIN_GROUP, EMPLOYEE_GROUP):
            group, created = Group.objects.get_or_create(name=name)
            groups[name] = group
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group: {name}"))
            else:
                self.stdout.write(f"Group already exists: {name}")

        for spec in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={
                    "email": spec["email"],
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "is_staff": spec["is_staff"],
                    "is_superuser": spec["is_superuser"],
                },
            )
            user.email = spec["email"]
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.is_staff = spec["is_staff"]
            user.is_superuser = spec["is_superuser"]
            user.set_password(spec["password"])
            user.save()
            user.groups.set([groups[spec["group"]]])
            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} user '{spec['username']}' "
                    f"(role: {spec['group']}, password: {spec['password']})"
                )
            )
