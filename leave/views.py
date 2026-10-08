"""Leave placeholder. Requests and approvals arrive in Week 5."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    return render(request, "leave/home.html")
