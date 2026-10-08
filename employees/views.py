"""Employee Management views. Add/edit/delete are Admin-only."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import admin_required
from accounts.roles import is_admin
from employees.forms import DepartmentForm, EmployeeForm
from employees.models import Department, Employee


def _can_view_employee(user, employee):
    if is_admin(user):
        return True
    profile = getattr(user, "employee_profile", None)
    return profile is not None and profile.pk == employee.pk


@admin_required
def employee_list(request):
    query = request.GET.get("q", "").strip()
    department_param = request.GET.get("department", "").strip()
    employees = Employee.objects.select_related("department", "user")

    if department_param:
        if department_param.isdigit():
            employees = employees.filter(department_id=int(department_param))
        else:
            employees = employees.filter(department__name__iexact=department_param)

    if query:
        employees = employees.annotate(
            full_name_annotated=Concat("first_name", Value(" "), "last_name")
        ).filter(
            Q(employee_id__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(full_name_annotated__icontains=query)
            | Q(email__icontains=query)
            | Q(department__name__icontains=query)
            | Q(job_title__icontains=query)
        )
    return render(
        request,
        "employees/list.html",
        {"employees": employees, "query": query},
    )


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(
        Employee.objects.select_related("department", "user"),
        pk=pk,
    )
    if not _can_view_employee(request.user, employee):
        return render(request, "403.html", status=403)
    return render(request, "employees/detail.html", {"employee": employee})


@login_required
def my_employee(request):
    employee = getattr(request.user, "employee_profile", None)
    if employee is None:
        return render(request, "employees/no_record.html")
    return redirect("employees:detail", pk=employee.pk)


@admin_required
def employee_create(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST, is_create=True)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f"Added employee {employee.employee_id}.")
            return redirect("employees:detail", pk=employee.pk)
    else:
        form = EmployeeForm(is_create=True)
    return render(
        request,
        "employees/form.html",
        {"form": form, "title": "Add employee", "submit_label": "Save employee"},
    )


@admin_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee, is_create=False)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f"Updated {employee.employee_id}.")
            return redirect("employees:detail", pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee, is_create=False)
    return render(
        request,
        "employees/form.html",
        {
            "form": form,
            "title": f"Edit {employee.employee_id}",
            "submit_label": "Save changes",
            "employee": employee,
        },
    )


@admin_required
def department_list(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f"Added department {department.name}.")
            return redirect("employees:departments")
    else:
        form = DepartmentForm()

    departments = Department.objects.annotate(headcount=Count("employees")).order_by("name")
    return render(
        request,
        "employees/departments.html",
        {"departments": departments, "form": form},
    )


@admin_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee.objects.select_related("user"), pk=pk)
    if request.method == "POST":
        employee_id = employee.employee_id
        user = employee.user
        employee.delete()
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(request, f"Deleted employee {employee_id}.")
        return redirect("employees:list")
    return render(request, "employees/confirm_delete.html", {"employee": employee})
