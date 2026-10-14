from django.urls import path

from timesheets import views

app_name = "timesheets"

urlpatterns = [
    path("", views.admin_timeline, name="timeline"),
    path("timeline/", views.admin_timeline, name="admin_timeline"),
]

