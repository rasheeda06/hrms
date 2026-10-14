from django.contrib import admin
from timesheets.models import Timesheet


@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "date",
        "clock_in",
        "clock_out",
        "break_duration_display",
        "net_working_hours_display",
        "status",
        "is_late",
    )
    list_filter = ("status", "is_late", "date", "employee__department")
    search_fields = (
        "employee__employee_id",
        "employee__first_name",
        "employee__last_name",
    )
    date_hierarchy = "date"
