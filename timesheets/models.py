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

    def _calc_minutes(self, t1, t2):
        """Calculates difference between two times on this date in minutes."""
        if not t1 or not t2:
            return 0
        dt1 = datetime.combine(self.date, t1)
        dt2 = datetime.combine(self.date, t2)
        if dt2 < dt1:
            dt2 += timedelta(days=1)
        return max(0, int((dt2 - dt1).total_seconds() // 60))

    def _format_minutes(self, mins):
        """Helper to format minutes into human-readable string like '4h 15m' or '45m'."""
        if mins <= 0:
            return "0m"
        hrs, m = divmod(mins, 60)
        if hrs > 0 and m > 0:
            return f"{hrs}h {m:02d}m"
        elif hrs > 0:
            return f"{hrs}h"
        return f"{m}m"

    @property
    def is_incomplete(self):
        """Returns True if the attendance record is incomplete (missing required milestones)."""
        if not self.clock_in:
            return True
        if not self.clock_out:
            return True
        if self.break_start and not self.break_end:
            return True
        return False

    @property
    def missing_events(self):
        """List of names of missing mandatory/expected timeline events."""
        missing = []
        if not self.clock_in:
            missing.append("Clock-in")
        if self.break_start and not self.break_end:
            missing.append("Break ended")
        if not self.clock_out:
            missing.append("Clock-out")
        return missing

    @property
    def missing_events_summary(self):
        """Human-readable string of missing events."""
        missing = self.missing_events
        return ", ".join(missing) if missing else "None"

    @property
    def timeline_events(self):
        """Returns ordered timeline events with icons, timestamps, descriptions, elapsed time, and missing flags."""
        def format_time(t):
            if not t:
                return None
            return t.strftime("%I:%M %p").lstrip("0")

        # Morning elapsed work (from clock_in to break_start or clock_out)
        morning_mins = 0
        if self.clock_in and self.break_start:
            morning_mins = self._calc_minutes(self.clock_in, self.break_start)
        elif self.clock_in and self.clock_out and not self.break_start:
            morning_mins = self._calc_minutes(self.clock_in, self.clock_out)

        # Afternoon elapsed work (from work_resume or break_end to clock_out)
        afternoon_mins = 0
        resume_ref = self.work_resume or self.break_end
        if resume_ref and self.clock_out:
            afternoon_mins = self._calc_minutes(resume_ref, self.clock_out)

        events = [
            {
                "id": "clock_in",
                "title": "Clock-in time",
                "time": format_time(self.clock_in),
                "raw_time": self.clock_in,
                "icon": "log-in",
                "badge_class": "hrms-timeline-blue" if self.clock_in else "hrms-timeline-missing",
                "description": f"Employee clocked in{' (Late Arrival)' if self.is_late else ' at the workplace'}." if self.clock_in else "Clock-in time was not recorded.",
                "is_completed": bool(self.clock_in),
                "is_missing": not bool(self.clock_in),
                "missing_label": "Missing Clock-in",
                "elapsed_text": None,
            },
            {
                "id": "work_start",
                "title": "Work started",
                "time": format_time(self.work_start),
                "raw_time": self.work_start,
                "icon": "play",
                "badge_class": "hrms-timeline-indigo" if self.work_start else "hrms-timeline-neutral",
                "description": "Shift work and daily assignments commenced." if self.work_start else "Work shift commenced at clock-in.",
                "is_completed": bool(self.work_start),
                "is_missing": False,
                "missing_label": None,
                "elapsed_text": None,
            },
            {
                "id": "break_start",
                "title": "Break started",
                "time": format_time(self.break_start),
                "raw_time": self.break_start,
                "icon": "coffee",
                "badge_class": "hrms-timeline-amber" if self.break_start else "hrms-timeline-neutral",
                "description": "Meal and rest break began." if self.break_start else "No break recorded for this shift.",
                "is_completed": bool(self.break_start),
                "is_missing": False,
                "missing_label": None,
                "elapsed_text": f"Work duration: {self._format_minutes(morning_mins)}" if morning_mins > 0 else None,
            },
            {
                "id": "break_end",
                "title": "Break ended",
                "time": format_time(self.break_end),
                "raw_time": self.break_end,
                "icon": "check-circle-2",
                "badge_class": "hrms-timeline-teal" if self.break_end else ("hrms-timeline-missing" if self.break_start else "hrms-timeline-neutral"),
                "description": f"Break concluded (Duration: {self.break_duration_display})." if self.break_end else ("Break end time was not logged." if self.break_start else "No break recorded."),
                "is_completed": bool(self.break_end),
                "is_missing": bool(self.break_start and not self.break_end),
                "missing_label": "Missing Break End",
                "elapsed_text": f"Break duration: {self.break_duration_display}" if self.break_start and self.break_end else None,
            },
            {
                "id": "work_resume",
                "title": "Work resumed",
                "time": format_time(self.work_resume),
                "raw_time": self.work_resume,
                "icon": "briefcase",
                "badge_class": "hrms-timeline-blue" if self.work_resume else ("hrms-timeline-missing" if self.break_end else "hrms-timeline-neutral"),
                "description": "Afternoon tasks and project execution resumed." if self.work_resume else ("Work resumption was not logged." if self.break_end else "Standard schedule continued."),
                "is_completed": bool(self.work_resume),
                "is_missing": bool(self.break_end and not self.work_resume),
                "missing_label": "Pending Resume",
                "elapsed_text": None,
            },
            {
                "id": "clock_out",
                "title": "Clock-out time",
                "time": format_time(self.clock_out),
                "raw_time": self.clock_out,
                "icon": "log-out",
                "badge_class": "hrms-timeline-purple" if self.clock_out else "hrms-timeline-missing",
                "description": f"Shift completed (Gross: {self.gross_working_hours_display}, Net: {self.net_working_hours_display})." if self.clock_out else ("Clock-out has not been recorded for this shift." if self.clock_in else "Not clocked out."),
                "is_completed": bool(self.clock_out),
                "is_missing": bool(self.clock_in and not self.clock_out),
                "missing_label": "Missing Clock-out",
                "elapsed_text": f"Work duration: {self._format_minutes(afternoon_mins)}" if afternoon_mins > 0 else (f"Work duration: {self._format_minutes(morning_mins)}" if morning_mins > 0 and not self.break_start else None),
            },
        ]
        return events

