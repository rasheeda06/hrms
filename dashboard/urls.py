from django.urls import path

from dashboard.views import home

app_name = "dashboard"

urlpatterns = [
    path("", home, name="home"),
]
