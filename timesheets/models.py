from datetime import datetime, time, timedelta

from django.db import models
from django.utils import timezone

from employees.models import Employee


class Timesheet(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        LATE = "late", "Late"
        HALF_DAY = "half_day", "Half Day"
        ABSENT = "absent", "Absent"
        ON_LEAVE = "on_leave", "On Leave"

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="timesheets",
    )
    date = models.DateField(default=timezone.localdate)

    clock_in = models.TimeField("Clock-in time", null=True, blank=True)
    work_start = models.TimeField("Work started", null=True, blank=True)
    break_start = models.TimeField("Break started", null=True, blank=True)
    break_end = models.TimeField("Break ended", null=True, blank=True)
    work_resume = models.TimeField("Work resumed", null=True, blank=True)
    clock_out = models.TimeField("Clock-out time", null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )
    is_late = models.BooleanField("Late arrival", default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "employee__employee_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "date"],
                name="unique_employee_date_timesheet",
            )
        ]

    def __str__(self):
        return f"{self.employee.employee_id} — {self.date} ({self.get_status_display()})"

    @property
    def gross_minutes(self):
        """Total duration from clock-in to clock-out in minutes."""
        if not self.clock_in or not self.clock_out:
            return 0
        t1 = datetime.combine(self.date, self.clock_in)
        t2 = datetime.combine(self.date, self.clock_out)
        if t2 < t1:
            t2 += timedelta(days=1)
        return max(0, int((t2 - t1).total_seconds() // 60))

    @property
    def break_minutes(self):
        """Total duration of break from break-start to break-end in minutes."""
        if not self.break_start or not self.break_end:
            return 0
        b1 = datetime.combine(self.date, self.break_start)
        b2 = datetime.combine(self.date, self.break_end)
        if b2 < b1:
            b2 += timedelta(days=1)
        return max(0, int((b2 - b1).total_seconds() // 60))

    @property
    def net_minutes(self):
        """Net working hours in minutes = gross minutes minus break duration."""
        return max(0, self.gross_minutes - self.break_minutes)

    @property
    def net_working_hours_display(self):
        """Formatted net working hours string, e.g. '8h 15m'."""
        mins = self.net_minutes
        hrs = mins // 60
        m = mins % 60
        return f"{hrs}h {m:02d}m"

    @property
    def gross_working_hours_display(self):
        """Formatted gross working hours string."""
        mins = self.gross_minutes
        hrs = mins // 60
        m = mins % 60
        return f"{hrs}h {m:02d}m"

    @property
    def break_duration_display(self):
        """Formatted break duration string, e.g. '45m' or '1h 15m'."""
        mins = self.break_minutes
        hrs = mins // 60
        m = mins % 60
        if hrs > 0:
            return f"{hrs}h {m:02d}m"
        return f"{m}m"

    @property
    def timeline_events(self):
        """Returns ordered timeline events with icons, timestamps, descriptions, and statuses."""
        def format_time(t):
            if not t:
                return None
            return t.strftime("%I:%M %p").lstrip("0")

        events = [
            {
                "id": "clock_in",
                "title": "Clock-in time",
                "time": format_time(self.clock_in),
                "raw_time": self.clock_in,
                "icon": "log-in",
                "badge_class": "hrms-timeline-blue",
                "description": f"Employee clocked in{' (Late Arrival)' if self.is_late else ' at the workplace'}.",
                "is_completed": bool(self.clock_in),
            },
            {
                "id": "work_start",
                "title": "Work started",
                "time": format_time(self.work_start),
                "raw_time": self.work_start,
                "icon": "play",
                "badge_class": "hrms-timeline-indigo",
                "description": "Shift work and daily assignments commenced.",
                "is_completed": bool(self.work_start),
            },
            {
                "id": "break_start",
                "title": "Break started",
                "time": format_time(self.break_start),
                "raw_time": self.break_start,
                "icon": "coffee",
                "badge_class": "hrms-timeline-amber",
                "description": "Meal and rest break began.",
                "is_completed": bool(self.break_start),
            },
            {
                "id": "break_end",
                "title": "Break ended",
                "time": format_time(self.break_end),
                "raw_time": self.break_end,
                "icon": "check-circle-2",
                "badge_class": "hrms-timeline-teal",
                "description": f"Break concluded (Duration: {self.break_duration_display}).",
                "is_completed": bool(self.break_end),
            },
            {
                "id": "work_resume",
                "title": "Work resumed",
                "time": format_time(self.work_resume),
                "raw_time": self.work_resume,
                "icon": "briefcase",
                "badge_class": "hrms-timeline-blue",
                "description": "Afternoon tasks and project execution resumed.",
                "is_completed": bool(self.work_resume),
            },
            {
                "id": "clock_out",
                "title": "Clock-out time",
                "time": format_time(self.clock_out),
                "raw_time": self.clock_out,
                "icon": "log-out",
                "badge_class": "hrms-timeline-purple",
                "description": f"Shift completed (Net Hours: {self.net_working_hours_display}).",
                "is_completed": bool(self.clock_out),
            },
        ]
        return events
