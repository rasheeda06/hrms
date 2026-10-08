from django.urls import path

from attendance import views

app_name = "attendance"

urlpatterns = [
    path("", views.home, name="home"),
]
