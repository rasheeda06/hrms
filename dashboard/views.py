"""Admin dashboard summary."""

from django.db.models import Count
from django.shortcuts import render

from accounts.decorators import admin_required
from employees.models import Department, Employee


@admin_required
def home(request):
    employees = Employee.objects.all()
    departments = (
        Department.objects.annotate(headcount=Count("employees"))
        .order_by("-headcount", "name")
    )

    context = {
        "total_employees": employees.filter(status=Employee.Status.ACTIVE).count(),
        "inactive_employees": employees.filter(status=Employee.Status.INACTIVE).count(),
        "department_count": departments.count(),
        "top_departments": departments[:5],
        "recent_employees": (
            employees.select_related("department").order_by("-date_of_joining")[:5]
        ),
        # Attendance (Week 4) and Leave (Week 5) have no models yet, so these
        # cards render an unavailable state instead of a fake number.
        "present_today": None,
        "on_leave_today": None,
    }
    return render(request, "dashboard/home.html", context)
