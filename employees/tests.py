from datetime import date

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from accounts.roles import ADMIN_GROUP, EMPLOYEE_GROUP
from employees.models import Department, Employee


class EmployeeManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_group = Group.objects.create(name=ADMIN_GROUP)
        cls.employee_group = Group.objects.create(name=EMPLOYEE_GROUP)
        cls.department = Department.objects.create(name="Engineering")

        cls.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="AdminPass123!",
        )
        cls.admin.groups.add(cls.admin_group)

        cls.employee_user = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="EmployeePass123!",
            first_name="Demo",
            last_name="Employee",
        )
        cls.employee_user.groups.add(cls.employee_group)

        cls.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="OtherPass123!",
            first_name="Other",
            last_name="Staff",
        )
        cls.other_user.groups.add(cls.employee_group)

        cls.own_record = Employee.objects.create(
            employee_id="EMP001",
            user=cls.employee_user,
            first_name="Demo",
            last_name="Employee",
            email="employee@example.com",
            phone="",
            department=cls.department,
            job_title="Staff Member",
            date_of_joining=date(2024, 1, 15),
            address="",
            status=Employee.Status.ACTIVE,
        )
        cls.other_record = Employee.objects.create(
            employee_id="EMP002",
            user=cls.other_user,
            first_name="Other",
            last_name="Staff",
            email="other@example.com",
            phone="",
            department=cls.department,
            job_title="Analyst",
            date_of_joining=date(2024, 2, 1),
            address="",
            status=Employee.Status.ACTIVE,
        )

    def test_week1_admin_login_still_goes_to_dashboard(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "admin", "password": "AdminPass123!"},
        )
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_week1_employee_login_still_goes_to_profile(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "employee", "password": "EmployeePass123!"},
        )
        self.assertRedirects(response, reverse("accounts:profile"))

    def test_admin_can_open_employee_list(self):
        self.client.login(username="admin", password="AdminPass123!")
        response = self.client.get(reverse("employees:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMP001")
        self.assertContains(response, "EMP002")

    def test_employee_cannot_open_list_or_add(self):
        self.client.login(username="employee", password="EmployeePass123!")
        list_response = self.client.get(reverse("employees:list"))
        add_response = self.client.get(reverse("employees:add"))
        self.assertEqual(list_response.status_code, 403)
        self.assertEqual(add_response.status_code, 403)

    def test_employee_cannot_post_add(self):
        self.client.login(username="employee", password="EmployeePass123!")
        response = self.client.post(
            reverse("employees:add"),
            {
                "employee_id": "EMP999",
                "username": "intruder",
                "password": "IntruderPass123!",
                "first_name": "No",
                "last_name": "Access",
                "email": "noaccess@example.com",
                "department": self.department.pk,
                "job_title": "Intern",
                "date_of_joining": "2024-03-01",
                "status": Employee.Status.ACTIVE,
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Employee.objects.filter(employee_id="EMP999").exists())

    def test_employee_can_view_own_record(self):
        self.client.login(username="employee", password="EmployeePass123!")
        response = self.client.get(reverse("employees:detail", args=[self.own_record.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMP001")
        self.assertContains(response, "Demo Employee")

    def test_employee_cannot_view_someone_else(self):
        self.client.login(username="employee", password="EmployeePass123!")
        response = self.client.get(reverse("employees:detail", args=[self.other_record.pk]))
        self.assertEqual(response.status_code, 403)

    def test_employee_cannot_edit_or_delete(self):
        self.client.login(username="employee", password="EmployeePass123!")
        edit_get = self.client.get(reverse("employees:edit", args=[self.own_record.pk]))
        delete_get = self.client.get(reverse("employees:delete", args=[self.own_record.pk]))
        self.assertEqual(edit_get.status_code, 403)
        self.assertEqual(delete_get.status_code, 403)

    def test_admin_can_add_employee(self):
        self.client.login(username="admin", password="AdminPass123!")
        response = self.client.post(
            reverse("employees:add"),
            {
                "employee_id": "EMP010",
                "username": "newstaff",
                "password": "NewStaffPass123!",
                "first_name": "New",
                "last_name": "Staff",
                "email": "newstaff@example.com",
                "phone": "5550100",
                "department": self.department.pk,
                "job_title": "Developer",
                "date_of_joining": "2024-04-01",
                "address": "1 Office Road",
                "status": Employee.Status.ACTIVE,
            },
        )
        employee = Employee.objects.get(employee_id="EMP010")
        self.assertRedirects(response, reverse("employees:detail", args=[employee.pk]))
        self.assertTrue(User.objects.filter(username="newstaff").exists())
        self.assertTrue(
            User.objects.get(username="newstaff").groups.filter(name=EMPLOYEE_GROUP).exists()
        )

    def test_admin_can_edit_employee(self):
        self.client.login(username="admin", password="AdminPass123!")
        response = self.client.post(
            reverse("employees:edit", args=[self.own_record.pk]),
            {
                "employee_id": "EMP001",
                "username": "employee",
                "first_name": "Demo",
                "last_name": "Employee",
                "email": "employee@example.com",
                "phone": "5550199",
                "department": self.department.pk,
                "job_title": "Senior Staff Member",
                "date_of_joining": "2024-01-15",
                "address": "",
                "status": Employee.Status.ACTIVE,
            },
        )
        self.assertRedirects(response, reverse("employees:detail", args=[self.own_record.pk]))
        self.own_record.refresh_from_db()
        self.assertEqual(self.own_record.job_title, "Senior Staff Member")
        self.assertEqual(self.own_record.phone, "5550199")

    def test_admin_can_delete_employee(self):
        self.client.login(username="admin", password="AdminPass123!")
        pk = self.other_record.pk
        user_id = self.other_user.pk
        response = self.client.post(reverse("employees:delete", args=[pk]))
        self.assertRedirects(response, reverse("employees:list"))
        self.assertFalse(Employee.objects.filter(pk=pk).exists())
        other = User.objects.get(pk=user_id)
        self.assertFalse(other.is_active)

    def test_my_information_redirects_to_own_record(self):
        self.client.login(username="employee", password="EmployeePass123!")
        response = self.client.get(reverse("employees:me"))
        self.assertRedirects(response, reverse("employees:detail", args=[self.own_record.pk]))

    def test_admin_can_search_by_department(self):
        self.client.login(username="admin", password="AdminPass123!")
        response = self.client.get(reverse("employees:list"), {"q": "Engineering"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMP001")
        self.assertContains(response, "EMP002")

    def test_admin_can_search_by_full_name(self):
        self.client.login(username="admin", password="AdminPass123!")
        response = self.client.get(reverse("employees:list"), {"q": "Demo Employee"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMP001")
        self.assertNotContains(response, "EMP002")

    def test_admin_can_filter_by_department_param(self):
        self.client.login(username="admin", password="AdminPass123!")
        response = self.client.get(reverse("employees:list"), {"department": self.department.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMP001")
        self.assertContains(response, "EMP002")

    def test_admin_departments_page_renders_view_employees_button(self):
        self.client.login(username="admin", password="AdminPass123!")
        response = self.client.get(reverse("employees:departments"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Employees")
        self.assertContains(response, "hrms-btn-view-dept")
        self.assertContains(response, "lucide-users")
        expected_url = f"{reverse('employees:list')}?department={self.department.pk}"
        self.assertContains(response, expected_url)

    def test_departments_view_employees_filter_isolates_department(self):
        empty_dept = Department.objects.create(name="Human Resources")
        self.client.login(username="admin", password="AdminPass123!")

        # Department with employees
        eng_response = self.client.get(
            reverse("employees:list"), {"department": self.department.pk}
        )
        self.assertEqual(eng_response.status_code, 200)
        self.assertContains(eng_response, "EMP001")
        self.assertContains(eng_response, "EMP002")

        # Department without employees
        hr_response = self.client.get(
            reverse("employees:list"), {"department": empty_dept.pk}
        )
        self.assertEqual(hr_response.status_code, 200)
        self.assertNotContains(hr_response, "EMP001")
        self.assertNotContains(hr_response, "EMP002")


