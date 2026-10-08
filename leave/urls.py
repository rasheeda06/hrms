from django.urls import path

from leave import views

app_name = "leave"

urlpatterns = [
    path("", views.home, name="home"),
]
