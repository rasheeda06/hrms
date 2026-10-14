from datetime import date, time, timedelta

from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from accounts.roles import ADMIN_GROUP, EMPLOYEE_GROUP
from employees.models import Department, Employee
from timesheets.models import Timesheet


class TimesheetModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.department = Department.objects.create(name="Engineering")
        cls.employee_user = User.objects.create_user(
            username="emp_john",
            email="john@example.com",
            password="TestPassword123!",
            first_name="John",
            last_name="Doe",
        )
        cls.employee = Employee.objects.create(
            employee_id="EMP101",
            user=cls.employee_user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            department=cls.department,
            job_title="Software Engineer",
            date_of_joining=date(2024, 1, 1),
            status=Employee.Status.ACTIVE,
        )

    def test_gross_and_net_working_hours_calculation(self):
        """Test gross, break, and net working hours calculation."""
        ts = Timesheet.objects.create(
            employee=self.employee,
            date=date(2026, 10, 14),
            clock_in=time(9, 0),
            work_start=time(9, 15),
            break_start=time(13, 0),
            break_end=time(13, 45),
            work_resume=time(13, 45),
            clock_out=time(18, 0),
            status=Timesheet.Status.PRESENT,
            is_late=False,
        )
        # Gross: 09:00 to 18:00 = 9 hours = 540 minutes
        self.assertEqual(ts.gross_minutes, 540)
        self.assertEqual(ts.gross_working_hours_display, "9h 00m")

        # Break: 13:00 to 13:45 = 45 minutes
        self.assertEqual(ts.break_minutes, 45)
        self.assertEqual(ts.break_duration_display, "45m")

        # Net: 540 - 45 = 495 minutes = 8h 15m
        self.assertEqual(ts.net_minutes, 495)
        self.assertEqual(ts.net_working_hours_display, "8h 15m")

    def test_timeline_events_structure(self):
        """Test that timeline_events returns 6 specific chronological events."""
        ts = Timesheet.objects.create(
            employee=self.employee,
            date=date(2026, 10, 14),
            clock_in=time(9, 0),
            work_start=time(9, 15),
            break_start=time(13, 0),
            break_end=time(13, 45),
            work_resume=time(13, 45),
            clock_out=time(18, 0),
            status=Timesheet.Status.PRESENT,
            is_late=False,
        )
        events = ts.timeline_events
        self.assertEqual(len(events), 6)

        event_ids = [e["id"] for e in events]
        self.assertEqual(
            event_ids,
            ["clock_in", "work_start", "break_start", "break_end", "work_resume", "clock_out"],
        )

        # Check titles
        self.assertEqual(events[0]["title"], "Clock-in time")
        self.assertEqual(events[1]["title"], "Work started")
        self.assertEqual(events[2]["title"], "Break started")
        self.assertEqual(events[3]["title"], "Break ended")
        self.assertEqual(events[4]["title"], "Work resumed")
        self.assertEqual(events[5]["title"], "Clock-out time")

        # Check completion and timestamps
        for e in events:
            self.assertTrue(e["is_completed"])
            self.assertIsNotNone(e["time"])

    def test_unique_employee_date_constraint(self):
        """Ensure an employee cannot have multiple records for the same date."""
        Timesheet.objects.create(
            employee=self.employee,
            date=date(2026, 10, 14),
            clock_in=time(9, 0),
        )
        with self.assertRaises(IntegrityError):
            Timesheet.objects.create(
                employee=self.employee,
                date=date(2026, 10, 14),
                clock_in=time(10, 0),
            )


class TimesheetViewAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_group = Group.objects.create(name=ADMIN_GROUP)
        cls.employee_group = Group.objects.create(name=EMPLOYEE_GROUP)
        cls.department = Department.objects.create(name="HR")

        cls.admin = User.objects.create_superuser(
            username="admin_user",
            email="admin@example.com",
            password="AdminPassword123!",
        )
        cls.admin.groups.add(cls.admin_group)

        cls.employee_user = User.objects.create_user(
            username="regular_emp",
            email="regular@example.com",
            password="EmpPassword123!",
        )
        cls.employee_user.groups.add(cls.employee_group)
        cls.employee = Employee.objects.create(
            employee_id="EMP201",
            user=cls.employee_user,
            first_name="Regular",
            last_name="Staff",
            email="regular@example.com",
            department=cls.department,
            job_title="HR Associate",
            date_of_joining=date(2024, 2, 1),
            status=Employee.Status.ACTIVE,
        )

    def test_unauthenticated_user_redirected_to_login(self):
        """Unauthenticated user accessing timeline should be redirected to login."""
        response = self.client.get(reverse("timesheets:timeline"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_regular_employee_forbidden(self):
        """Regular employee must not access the admin timesheet page (403 Forbidden)."""
        self.client.login(username="regular_emp", password="EmpPassword123!")
        response = self.client.get(reverse("timesheets:timeline"))
        self.assertEqual(response.status_code, 403)

    def test_admin_user_can_access(self):
        """Admin user can access the timesheet timeline successfully (200 OK)."""
        self.client.login(username="admin_user", password="AdminPassword123!")
        response = self.client.get(reverse("timesheets:timeline"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "timesheets/timeline.html")


class TimesheetTimelineDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_group = Group.objects.create(name=ADMIN_GROUP)
        cls.employee_group = Group.objects.create(name=EMPLOYEE_GROUP)
        cls.department = Department.objects.create(name="Product")

        cls.admin = User.objects.create_superuser(
            username="admin_timeline",
            email="admin_timeline@example.com",
            password="AdminPassword123!",
        )
        cls.admin.groups.add(cls.admin_group)

        cls.emp_user = User.objects.create_user(
            username="emp_alex",
            email="alex@example.com",
            password="AlexPassword123!",
        )
        cls.emp_user.groups.add(cls.employee_group)
        cls.employee = Employee.objects.create(
            employee_id="EMP301",
            user=cls.emp_user,
            first_name="Alex",
            last_name="Rivers",
            email="alex@example.com",
            department=cls.department,
            job_title="Product Designer",
            date_of_joining=date(2024, 3, 1),
            status=Employee.Status.ACTIVE,
        )

        cls.timesheet = Timesheet.objects.create(
            employee=cls.employee,
            date=date(2026, 10, 14),
            clock_in=time(9, 0),
            work_start=time(9, 15),
            break_start=time(13, 0),
            break_end=time(13, 45),
            work_resume=time(13, 45),
            clock_out=time(18, 0),
            status=Timesheet.Status.PRESENT,
            is_late=False,
            notes="Sprint review and UI design handoff.",
        )

    def setUp(self):
        self.client.login(username="admin_timeline", password="AdminPassword123!")

    def test_weekly_project_timesheet_table_renders(self):
        """Weekly project table displays projects, tasks, day columns, and totals."""
        response = self.client.get(
            reverse("timesheets:timeline"),
            {"date": "2026-10-14", "employee": self.employee.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alex Rivers")
        self.assertContains(response, "EMP301")
        self.assertContains(response, "timesheet-table")
        self.assertContains(response, "PROJECTS")
        self.assertContains(response, "TOTAL")
        self.assertContains(response, "Cardy Product Demo")
        self.assertContains(response, "Time Off: Paid Leave")
        self.assertContains(response, "Add Time Entry")
        self.assertContains(response, "Save as Draft")
        self.assertContains(response, "Submit Timesheet")

    def test_summary_metric_cards_and_9h_allocation(self):
        """Top metric summary cards and 9-hour daily allocation modal are present."""
        response = self.client.get(
            reverse("timesheets:timeline"),
            {"date": "2026-10-14", "employee": self.employee.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Working Hours")
        self.assertContains(response, "Billable")
        self.assertContains(response, "Non Billable")
        self.assertContains(response, "Time Off")
        # 9-hour allocation feature
        self.assertContains(response, "dayAllocationModal")
        self.assertContains(response, "Daily 9-Hour Work Allocation")

    def test_quick_date_buttons_and_week_navigation(self):
        """Quick date buttons (Previous Day, Next Day, Today) and week navigation are present."""
        response = self.client.get(
            reverse("timesheets:timeline"),
            {"date": "2026-10-14"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Previous Day")
        self.assertContains(response, "Next Day")
        self.assertContains(response, "Today")
        self.assertContains(response, "date=2026-10-13")
        self.assertContains(response, "date=2026-10-15")

    def test_sidebar_timesheet_link_displayed_for_admin(self):
        """Timesheet navigation link is visible in the sidebar for admin users."""
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Timesheet")
        self.assertContains(response, reverse("timesheets:timeline"))

    def test_add_task_entry_via_post(self):
        """Can add a new time entry with project, task, date, and hours via POST."""
        post_data = {
            "employee_id": self.employee.pk,
            "project_name": "New Website Project",
            "task_name": "API Endpoint Integration",
            "entry_date": "2026-10-14",
            "hours": "04:30",
            "notes": "Building REST endpoints",
        }
        response = self.client.post(reverse("timesheets:add_task_entry"), post_data)
        self.assertEqual(response.status_code, 302)

        # Verify page now shows new project and task
        timeline_res = self.client.get(
            reverse("timesheets:timeline"),
            {"date": "2026-10-14", "employee": self.employee.pk},
        )
        self.assertEqual(timeline_res.status_code, 200)
        self.assertContains(timeline_res, "New Website Project")
        self.assertContains(timeline_res, "API Endpoint Integration")

    def test_save_and_submit_timesheet_action(self):
        """Submitting timesheet updates status to SUBMITTED."""
        # Load page first to seed weekly timesheet
        self.client.get(
            reverse("timesheets:timeline"),
            {"date": "2026-10-14", "employee": self.employee.pk},
        )
        post_data = {
            "employee_id": self.employee.pk,
            "week_start": "2026-10-12",
            "action_type": "submit",
        }
        response = self.client.post(reverse("timesheets:save_timesheet"), post_data)
        self.assertEqual(response.status_code, 302)
