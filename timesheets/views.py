"""Admin Timesheet views. Exclusively for Admin users."""

from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from accounts.decorators import admin_required
from employees.models import Department, Employee
from timesheets.models import Timesheet


@admin_required
def admin_timeline(request):
    """Admin-only Daily Timeline dashboard for employee timesheets."""
    today = timezone.localdate()

    # Parse selected date from GET parameter (YYYY-MM-DD)
    date_param = request.GET.get("date", "").strip()
    selected_date = today
    if date_param:
        try:
            selected_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today

    # Previous, Next, and Today dates for quick buttons
    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)

    # Department filter
    dept_param = request.GET.get("department", "").strip()
    departments = Department.objects.all().order_by("name")
    selected_dept = None
    if dept_param and dept_param.isdigit():
        selected_dept = departments.filter(pk=int(dept_param)).first()

    # Employee queryset
    employees = Employee.objects.select_related("department", "user").filter(
        status=Employee.Status.ACTIVE
    )
    if selected_dept:
        employees = employees.filter(department=selected_dept)

    # Selected employee
    emp_param = request.GET.get("employee", "").strip()
    selected_employee = None
    if emp_param:
        if emp_param.isdigit():
            selected_employee = employees.filter(pk=int(emp_param)).first()
        if not selected_employee:
            selected_employee = employees.filter(employee_id__iexact=emp_param).first()

    # If no employee specified or found, default to first employee in list
    if not selected_employee and employees.exists():
        selected_employee = employees.first()

    # Fetch daily timesheet record for selected employee on selected date
    timesheet_record = None
    if selected_employee:
        timesheet_record = Timesheet.objects.filter(
            employee=selected_employee,
            date=selected_date,
        ).first()

    # Prepare summary card metrics for selected employee & date
    if timesheet_record:
        total_working_hours = timesheet_record.net_working_hours_display
        gross_working_hours = timesheet_record.gross_working_hours_display
        break_duration = timesheet_record.break_duration_display
        break_minutes = timesheet_record.break_minutes
        if timesheet_record.is_late:
            late_status = "Late arrival"
            late_badge_class = "text-bg-warning"
        else:
            late_status = "On time"
            late_badge_class = "text-bg-success"
        attendance_status = timesheet_record.get_status_display()
        timeline_events = timesheet_record.timeline_events
        has_record = True
    else:
        total_working_hours = "0h 00m"
        gross_working_hours = "0h 00m"
        break_duration = "0m"
        break_minutes = 0
        late_status = "—"
        late_badge_class = "text-bg-secondary"
        attendance_status = "No Record"
        timeline_events = []
        has_record = False

    # Calculate weekly strip navigation (Monday to Sunday around selected_date)
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    week_days = []
    for i in range(7):
        d = start_of_week + timedelta(days=i)
        week_days.append({
            "date": d,
            "date_str": d.strftime("%Y-%m-%d"),
            "day_name": d.strftime("%a"),
            "day_num": d.strftime("%d"),
            "is_selected": d == selected_date,
            "is_today": d == today,
        })
    prev_week_date = start_of_week - timedelta(days=7)
    next_week_date = start_of_week + timedelta(days=7)

    # Attach selected_date status for each employee in the sidebar employee list
    employee_records_map = {}
    if employees.exists():
        records = Timesheet.objects.filter(
            employee__in=employees,
            date=selected_date,
        ).select_related("employee")
        for r in records:
            employee_records_map[r.employee_id] = r

    employee_list_data = []
    for emp in employees:
        rec = employee_records_map.get(emp.employee_id)
        employee_list_data.append({
            "employee": emp,
            "is_selected": selected_employee and emp.pk == selected_employee.pk,
            "record": rec,
            "status": rec.get_status_display() if rec else "No Record",
            "net_hours": rec.net_working_hours_display if rec else "0h",
            "is_late": rec.is_late if rec else False,
        })

    context = {
        "selected_date": selected_date,
        "selected_date_str": selected_date.strftime("%Y-%m-%d"),
        "prev_date_str": prev_date.strftime("%Y-%m-%d"),
        "next_date_str": next_date.strftime("%Y-%m-%d"),
        "today_str": today.strftime("%Y-%m-%d"),
        "departments": departments,
        "selected_dept": selected_dept,
        "employees": employees,
        "selected_employee": selected_employee,
        "timesheet_record": timesheet_record,
        "has_record": has_record,
        "timeline_events": timeline_events,
        "total_working_hours": total_working_hours,
        "gross_working_hours": gross_working_hours,
        "break_duration": break_duration,
        "break_minutes": break_minutes,
        "late_status": late_status,
        "late_badge_class": late_badge_class,
        "attendance_status": attendance_status,
        "week_days": week_days,
        "start_of_week": start_of_week,
        "prev_week_str": prev_week_date.strftime("%Y-%m-%d"),
        "next_week_str": next_week_date.strftime("%Y-%m-%d"),
        "employee_list_data": employee_list_data,
    }
    return render(request, "timesheets/timeline.html", context)
