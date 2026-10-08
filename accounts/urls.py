from django.contrib.auth.views import LogoutView
from django.urls import path

from accounts.views import RoleLoginView, profile

app_name = "accounts"

urlpatterns = [
    path("login/", RoleLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", profile, name="profile"),
]
