from datetime import date

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from employees.models import Department, Employee


class Command(BaseCommand):
    help = "Create sample departments and link the demo employee login to a record."

    def handle(self, *args, **options):
        hr, _ = Department.objects.get_or_create(name="Human Resources")
        engineering, _ = Department.objects.get_or_create(name="Engineering")
        self.stdout.write(self.style.SUCCESS("Departments ready: Human Resources, Engineering"))

        try:
            user = User.objects.get(username="employee")
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(
                    "No user named 'employee'. Run python manage.py seed_users first."
                )
            )
            return

        employee, created = Employee.objects.get_or_create(
            user=user,
            defaults={
                "employee_id": "EMP001",
                "first_name": user.first_name or "Demo",
                "last_name": user.last_name or "Employee",
                "email": user.email or "employee@example.com",
                "phone": "",
                "department": engineering,
                "job_title": "Staff Member",
                "date_of_joining": date(2024, 1, 15),
                "address": "",
                "status": Employee.Status.ACTIVE,
            },
        )
        action = "Created" if created else "Already exists"
        self.stdout.write(
            self.style.SUCCESS(f"{action}: {employee.employee_id} for user '{user.username}'")
        )
        self.stdout.write(f"Also available: {hr.name}")
