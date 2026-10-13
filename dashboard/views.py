"""Admin dashboard summary."""

from django.apps import apps
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import admin_required
from employees.models import Department, Employee


@admin_required
def home(request):
    employees = Employee.objects.all()
    departments = (
        Department.objects.annotate(headcount=Count("employees"))
        .order_by("-headcount", "name")
    )

    total_employees = employees.count()
    active_employees = employees.filter(status=Employee.Status.ACTIVE).count()
    inactive_employees = employees.filter(status=Employee.Status.INACTIVE).count()
    department_count = departments.count()

    # Present today: query from attendance records if model exists, otherwise active employees in DB
    present_today = active_employees
    try:
        if apps.is_installed("attendance"):
            Attendance = apps.get_model("attendance", "Attendance", require_ready=False)
            if Attendance and hasattr(Attendance, "objects"):
                today = timezone.localdate()
                present_today = Attendance.objects.filter(date=today, status="present").count()
    except Exception:
        pass

    # On leave today: query from leave records if model exists, otherwise inactive employees in DB
    on_leave_today = inactive_employees
    try:
        if apps.is_installed("leave"):
            LeaveModel = apps.get_model("leave", "LeaveRequest", require_ready=False)
            if LeaveModel and hasattr(LeaveModel, "objects"):
                today = timezone.localdate()
                on_leave_today = LeaveModel.objects.filter(
                    start_date__lte=today, end_date__gte=today, status="approved"
                ).count()
    except Exception:
        pass

    context = {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "department_count": department_count,
        "present_today": present_today,
        "on_leave_today": on_leave_today,
        "top_departments": departments[:5],
        "recent_employees": (
            employees.select_related("department").order_by("-date_of_joining")[:5]
        ),
    }
    return render(request, "dashboard/home.html", context)
