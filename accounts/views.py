"""Login, logout redirect, and Week 1 placeholder pages."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse

from accounts.roles import is_admin


class RoleLoginView(LoginView):
    """Django's login form, then send Admin and Employee to different pages."""

    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        if is_admin(self.request.user):
            return reverse("dashboard:home")
        return reverse("accounts:profile")


def home(request):
    """Site root: login if needed, otherwise the page for this role."""
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if is_admin(request.user):
        return redirect("dashboard:home")
    return redirect("accounts:profile")


@login_required
def profile(request):
    """Employee landing page (placeholder until Week 2 employee profiles)."""
    return render(request, "accounts/profile.html")
