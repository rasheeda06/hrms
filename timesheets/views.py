"""Admin Timesheet views. Exclusively for Admin users."""

from datetime import date, datetime, timedelta
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required
from employees.models import Department, Employee
from timesheets.models import (
    Timesheet,
    Project,
    ProjectMilestone,
    ProjectTask,
    WeeklyTimesheet,
    TimesheetTaskRow,
    TimesheetDailyCell,
)





@admin_required
def admin_timeline(request):
    """Admin-only Weekly Project Timesheet Management dashboard for employees."""
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

    # Default to first employee if none selected
    if not selected_employee and employees.exists():
        selected_employee = employees.first()

    # Monday start of week for the selected date
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    week_range_str = f"{start_of_week.strftime('%d/%b/%Y')} - {end_of_week.strftime('%d/%b/%Y')}"

    # Previous and Next week dates
    prev_week_date = start_of_week - timedelta(days=7)
    next_week_date = start_of_week + timedelta(days=7)

    # Weekly Timesheet for selected employee
    weekly_timesheet = None
    task_rows = []
    day_totals = [0] * 7
    day_totals_display = ["0:00"] * 7
    grand_total_minutes = 0
    grand_total_display = "0:00"

    if selected_employee:
        weekly_timesheet, created = WeeklyTimesheet.objects.get_or_create(
            employee=selected_employee,
            week_start_date=start_of_week,
            defaults={"status": "draft"}
        )

        # Prefetch task rows and daily cells
        task_rows = list(weekly_timesheet.rows.prefetch_related("cells").all())

        # Compute totals across 7 days
        for row in task_rows:
            cells_map = {c.day_index: c for c in row.cells.all()}
            row_cells_list = []
            for i in range(7):
                cell = cells_map.get(i)
                if not cell:
                    cell = TimesheetDailyCell.objects.create(
                        row=row,
                        date=start_of_week + timedelta(days=i),
                        day_index=i,
                        hours_minutes=0,
                        hours_str="0:00",
                    )
                row_cells_list.append(cell)
                day_totals[i] += cell.hours_minutes
            row.ordered_cells = row_cells_list

        for i in range(7):
            mins = day_totals[i]
            hrs, m = divmod(mins, 60)
            day_totals_display[i] = f"{hrs:d}:{m:02d}" if mins > 0 else "0:00"

        grand_total_minutes = sum(day_totals)
        gt_hrs, gt_m = divmod(grand_total_minutes, 60)
        grand_total_display = f"{gt_hrs:02d}:{gt_m:02d}" if grand_total_minutes > 0 else "0:00"

    # Days list for the table header (MON..SUN)
    week_days = []
    for i in range(7):
        d = start_of_week + timedelta(days=i)
        is_today = (d == today)

        target_minutes = 540  # 9 hours standard working day
        actual_minutes = day_totals[i]
        percentage = min(100, int((actual_minutes / target_minutes) * 100)) if target_minutes else 0
        is_target_met = actual_minutes >= target_minutes

        tasks_on_day = []
        for r in task_rows:
            c = next((cell for cell in r.ordered_cells if cell.day_index == i), None)
            if c and c.hours_minutes > 0:
                tasks_on_day.append({
                    "project_name": r.project_name,
                    "milestone_name": r.milestone_name,
                    "task_name": r.task_name,
                    "entry_type": r.entry_type,
                    "hours_str": c.hours_str,
                    "hours_minutes": c.hours_minutes,
                    "notes": c.notes,
                })

        day_info = {
            "date": d,
            "date_str": d.strftime("%Y-%m-%d"),
            "date_formatted": d.strftime("%d/%b/%Y"),
            "day_name": d.strftime("%a").upper(),
            "day_num": d.strftime("%d"),
            "day_index": i,
            "is_selected": d == selected_date,
            "is_today": is_today,
            "has_leave": False,
            "total_hours": day_totals_display[i],
            "total_minutes": actual_minutes,
            "target_minutes": target_minutes,
            "is_target_met": is_target_met,
            "percentage": percentage,
            "tasks_breakdown": tasks_on_day,
        }
        week_days.append(day_info)

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
        emp_status = rec.get_status_display() if rec else "Active"
        employee_list_data.append({
            "employee": emp,
            "is_selected": selected_employee and emp.pk == selected_employee.pk,
            "record": rec,
            "status": emp_status,
            "is_incomplete": rec.is_incomplete if rec else False,
            "net_hours": rec.net_working_hours_display if rec else "9h",
            "is_late": rec.is_late if rec else False,
        })

    # Available projects for modal dropdowns (clean, user projects)
    projects = Project.objects.filter(is_active=True).prefetch_related("milestones", "tasks")

    # Fetch daily record if present for backward compatibility
    timesheet_record = None
    if selected_employee:
        timesheet_record = Timesheet.objects.filter(
            employee=selected_employee,
            date=selected_date,
        ).first()

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
        "week_days": week_days,
        "start_of_week": start_of_week,
        "end_of_week": end_of_week,
        "week_range_str": week_range_str,
        "prev_week_str": prev_week_date.strftime("%Y-%m-%d"),
        "next_week_str": next_week_date.strftime("%Y-%m-%d"),
        "employee_list_data": employee_list_data,
        "projects": projects,
        # Weekly project table context
        "weekly_timesheet": weekly_timesheet,
        "task_rows": task_rows,
        "day_totals_display": day_totals_display,
        "grand_total_display": grand_total_display,
        "grand_total_minutes": grand_total_minutes,
        "summary_working_hours": grand_total_display,
        "summary_billable": grand_total_display,
        "summary_non_billable": "0:00",
        "summary_time_off": "0:00",
        # Compatibility fields
        "timesheet_record": timesheet_record,
        "has_record": bool(timesheet_record) or bool(weekly_timesheet),
        "total_working_hours": grand_total_display,
        "gross_working_hours": grand_total_display,
        "break_duration": "45m",
        "clock_in_time": "9:00 AM",
        "clock_out_time": "6:00 PM",
        "is_incomplete": False,
        "attendance_status": "Present",
        "attendance_badge_class": "text-bg-success",
        "late_status": "On time",
        "late_badge_class": "text-bg-success",
        "timeline_events": timesheet_record.timeline_events if timesheet_record else [],
    }
    return render(request, "timesheets/timeline.html", context)


@admin_required
@require_POST
def save_timesheet(request):
    """Save timesheet cells, status, and certification flag via AJAX or POST."""
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    else:
        data = request.POST

    timesheet_id = data.get("timesheet_id")
    weekly_ts = None
    if timesheet_id:
        weekly_ts = WeeklyTimesheet.objects.filter(pk=timesheet_id).first()

    if not weekly_ts:
        emp_id = data.get("employee_id") or data.get("employee")
        date_param = data.get("week_start") or data.get("entry_date") or data.get("date")
        if emp_id:
            emp = Employee.objects.filter(pk=emp_id).first()
            if emp:
                if date_param:
                    try:
                        d = datetime.strptime(str(date_param), "%Y-%m-%d").date()
                    except ValueError:
                        d = timezone.localdate()
                else:
                    d = timezone.localdate()
                start_of_week = d - timedelta(days=d.weekday())
                weekly_ts, _ = WeeklyTimesheet.objects.get_or_create(
                    employee=emp,
                    week_start_date=start_of_week,
                    defaults={"status": "draft"}
                )

    if not weekly_ts:
        raise Http404("Weekly timesheet not found")

    action = data.get("action") or data.get("action_type") or "save"
    if action == "submit":
        weekly_ts.status = "submitted"
    elif action == "approve":
        weekly_ts.status = "approved"
    elif action == "draft":
        weekly_ts.status = "draft"

    if "certified" in data:
        weekly_ts.certified = bool(data.get("certified"))
    weekly_ts.save()

    entries = data.get("entries", [])
    if isinstance(entries, str):
        try:
            entries = json.loads(entries)
        except ValueError:
            entries = []

    for entry in entries:
        cell_id = entry.get("cell_id")
        hours_str = entry.get("hours", "0:00")
        notes = entry.get("notes")
        if cell_id:
            cell = TimesheetDailyCell.objects.filter(pk=cell_id).first()
            if cell:
                cell.set_time(hours_str, notes)
                cell.save()

    if not (request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json"):
        return redirect(f"/timesheets/?date={weekly_ts.week_start_date}&employee={weekly_ts.employee_id}")

    day_totals = [weekly_ts.get_day_display(i) for i in range(7)]
    return JsonResponse({
        "status": "success",
        "message": "Timesheet saved successfully",
        "timesheet_status": weekly_ts.get_status_display(),
        "total_hours": weekly_ts.total_hours_display,
        "day_totals": day_totals,
    })


@admin_required
@require_POST
def add_task_entry(request):
    """Add a new project/milestone task row to the weekly timesheet."""
    timesheet_id = request.POST.get("timesheet_id")
    weekly_ts = None
    if timesheet_id:
        weekly_ts = WeeklyTimesheet.objects.filter(pk=timesheet_id).first()

    if not weekly_ts:
        emp_id = request.POST.get("employee_id") or request.POST.get("employee")
        date_param = request.POST.get("entry_date") or request.POST.get("date") or request.POST.get("week_start")
        if emp_id:
            emp = Employee.objects.filter(pk=emp_id).first()
            if emp:
                if date_param:
                    try:
                        d = datetime.strptime(str(date_param), "%Y-%m-%d").date()
                    except ValueError:
                        d = timezone.localdate()
                else:
                    d = timezone.localdate()
                start_of_week = d - timedelta(days=d.weekday())
                weekly_ts, _ = WeeklyTimesheet.objects.get_or_create(
                    employee=emp,
                    week_start_date=start_of_week,
                    defaults={"status": "draft"}
                )

    if not weekly_ts:
        raise Http404("Weekly timesheet not found")

    custom_proj = request.POST.get("custom_project_name", "").strip()
    project_name = request.POST.get("project_name", "").strip()
    if (not project_name or project_name == "__NEW__") and custom_proj:
        project_name = custom_proj
    if not project_name:
        project_name = "General Project"

    entry_type = request.POST.get("entry_type", "task").strip()

    if entry_type == "meeting":
        meeting_title = request.POST.get("meeting_title", "").strip()
        task_name = meeting_title or request.POST.get("task_name", "").strip() or "Meeting"
        meeting_type = request.POST.get("meeting_type", "").strip()
        platform = request.POST.get("meeting_platform", "").strip()
        milestone_parts = [p for p in [meeting_type, platform] if p]
        milestone_name = " — ".join(milestone_parts) if milestone_parts else (request.POST.get("milestone_name", "").strip() or "Meeting")
        hours_param = request.POST.get("meeting_hours", "").strip() or request.POST.get("hours", "").strip()
        day_index_param = request.POST.get("meeting_day_index") if request.POST.get("meeting_day_index") is not None else request.POST.get("day_index")
        notes_param = request.POST.get("meeting_notes", "").strip() or request.POST.get("notes", "").strip()
    else:
        task_name = request.POST.get("task_name", "").strip() or "Standard Task"
        milestone_name = request.POST.get("milestone_name", "").strip()
        task_category = request.POST.get("task_category", "").strip()
        if not milestone_name and task_category:
            milestone_name = task_category
        elif milestone_name and task_category and task_category not in milestone_name:
            milestone_name = f"{milestone_name} ({task_category})"
        hours_param = request.POST.get("hours", "").strip()
        day_index_param = request.POST.get("day_index")
        notes_param = request.POST.get("notes", "").strip()

    proj, _ = Project.objects.get_or_create(name=project_name)
    if milestone_name:
        ProjectMilestone.objects.get_or_create(project=proj, name=milestone_name)

    order = weekly_ts.rows.count()
    row = TimesheetTaskRow.objects.create(
        weekly_timesheet=weekly_ts,
        project=proj,
        project_name=project_name,
        milestone_name=milestone_name,
        task_name=task_name,
        entry_type=entry_type,
        order=order,
    )

    entry_date_param = request.POST.get("entry_date", "").strip()
    target_day_index = None
    if day_index_param is not None and str(day_index_param).strip() != "":
        try:
            target_day_index = int(day_index_param)
        except ValueError:
            target_day_index = None
    elif entry_date_param:
        try:
            ed = datetime.strptime(entry_date_param, "%Y-%m-%d").date()
            target_day_index = (ed - weekly_ts.week_start_date).days
        except ValueError:
            target_day_index = None

    notes_param = request.POST.get("notes", "").strip()

    cells = []
    for i in range(7):
        cell_date = weekly_ts.week_start_date + timedelta(days=i)
        initial_hours = "0:00"
        initial_notes = ""
        if target_day_index is not None and i == target_day_index and hours_param:
            initial_hours = hours_param
            initial_notes = notes_param

        c = TimesheetDailyCell.objects.create(
            row=row,
            date=cell_date,
            day_index=i,
            hours_minutes=0,
            hours_str="0:00",
            notes=initial_notes,
        )
        if initial_hours != "0:00":
            c.set_time(initial_hours, initial_notes)
            c.save()
        cells.append({"id": c.pk, "day_index": i, "hours": initial_hours})

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
        return JsonResponse({
            "status": "success",
            "row_id": row.pk,
            "project_name": row.project_name,
            "milestone_name": row.milestone_name,
            "task_name": row.task_name,
            "cells": cells,
        })

    return redirect(f"/timesheets/?date={weekly_ts.week_start_date}&employee={weekly_ts.employee_id}")


@admin_required
def delete_task_row(request, row_id):
    """Delete a task row from the weekly timesheet."""
    row = get_object_or_404(TimesheetTaskRow, pk=row_id)
    weekly_ts = row.weekly_timesheet
    row.delete()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "status": "success",
            "message": "Row deleted",
            "total_hours": weekly_ts.total_hours_display,
        })
    return redirect(f"/timesheets/?date={weekly_ts.week_start_date}&employee={weekly_ts.employee_id}")


@admin_required
def copy_last_week(request):
    """Copy task rows from previous week into the current week timesheet."""
    timesheet_id = request.GET.get("timesheet_id") or request.POST.get("timesheet_id")
    weekly_ts = get_object_or_404(WeeklyTimesheet, pk=timesheet_id)

    last_week_start = weekly_ts.week_start_date - timedelta(days=7)
    prev_ts = WeeklyTimesheet.objects.filter(
        employee=weekly_ts.employee,
        week_start_date=last_week_start
    ).first()

    copied_count = 0
    if prev_ts and prev_ts.rows.exists():
        for r in prev_ts.rows.all():
            new_row = TimesheetTaskRow.objects.create(
                weekly_timesheet=weekly_ts,
                project=r.project,
                project_name=r.project_name,
                milestone_name=r.milestone_name,
                task_name=r.task_name,
                entry_type=r.entry_type,
                order=weekly_ts.rows.count(),
            )
            for i in range(7):
                TimesheetDailyCell.objects.create(
                    row=new_row,
                    date=weekly_ts.week_start_date + timedelta(days=i),
                    day_index=i,
                    hours_minutes=0,
                    hours_str="0:00",
                    notes="",
                )
            copied_count += 1

    return redirect(f"/timesheets/?date={weekly_ts.week_start_date}&employee={weekly_ts.employee_id}")
