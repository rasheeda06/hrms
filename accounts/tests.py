from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from accounts.roles import ADMIN_GROUP, EMPLOYEE_GROUP, is_admin, is_employee


class RoleHelperTests(TestCase):
    def setUp(self):
        self.admin_group = Group.objects.create(name=ADMIN_GROUP)
        self.employee_group = Group.objects.create(name=EMPLOYEE_GROUP)

    def test_admin_group_user_is_admin(self):
        user = User.objects.create_user(username="hr", password="TestPass123!")
        user.groups.add(self.admin_group)
        self.assertTrue(is_admin(user))
        self.assertFalse(is_employee(user))

    def test_employee_group_user_is_employee(self):
        user = User.objects.create_user(username="staff", password="TestPass123!")
        user.groups.add(self.employee_group)
        self.assertTrue(is_employee(user))
        self.assertFalse(is_admin(user))


class LoginFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        admin_group = Group.objects.create(name=ADMIN_GROUP)
        employee_group = Group.objects.create(name=EMPLOYEE_GROUP)

        cls.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="AdminPass123!",
        )
        cls.admin.groups.add(admin_group)

        cls.employee = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="EmployeePass123!",
        )
        cls.employee.groups.add(employee_group)

    def test_guest_is_sent_to_login(self):
        response = self.client.get("/")
        self.assertRedirects(response, reverse("accounts:login"))

    def test_admin_login_goes_to_dashboard(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "admin", "password": "AdminPass123!"},
        )
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_employee_login_goes_to_profile(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "employee", "password": "EmployeePass123!"},
        )
        self.assertRedirects(response, reverse("accounts:profile"))

    def test_employee_cannot_open_dashboard(self):
        self.client.login(username="employee", password="EmployeePass123!")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_open_dashboard(self):
        self.client.login(username="admin", password="AdminPass123!")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username="employee", password="EmployeePass123!")
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        follow = self.client.get("/")
        self.assertRedirects(follow, reverse("accounts:login"))
