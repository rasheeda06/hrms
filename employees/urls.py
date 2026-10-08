from django.urls import path

from employees import views

app_name = "employees"

urlpatterns = [
    path("", views.employee_list, name="list"),
    path("add/", views.employee_create, name="add"),
    path("me/", views.my_employee, name="me"),
    path("departments/", views.department_list, name="departments"),
    path("<int:pk>/", views.employee_detail, name="detail"),
    path("<int:pk>/edit/", views.employee_edit, name="edit"),
    path("<int:pk>/delete/", views.employee_delete, name="delete"),
]
