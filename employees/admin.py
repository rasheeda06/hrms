from django.contrib import admin

from employees.models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "department",
        "job_title",
        "status",
        "date_of_joining",
    )
    list_filter = ("status", "department")
    search_fields = ("employee_id", "first_name", "last_name", "email")
    autocomplete_fields = ("user", "department")
    ordering = ("employee_id",)
