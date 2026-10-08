"""Attendance placeholder. Real punch in/out arrives in Week 4."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    return render(request, "attendance/home.html")
