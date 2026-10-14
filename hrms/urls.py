"""Root URL routes for the HRMS project."""

from django.contrib import admin
from django.urls import include, path

from accounts.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("employees/", include("employees.urls")),
    path("attendance/", include("attendance.urls")),
    path("timesheets/", include("timesheets.urls")),
    path("leave/", include("leave.urls")),
]
