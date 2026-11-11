from django.contrib.auth import login
from django.shortcuts import redirect, render

from faces.services import get_current_template

from .forms import SignUpForm


def home_view(request):
    if request.user.is_authenticated:
        return redirect("profile")
    return redirect("login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("profile")
    else:
        form = SignUpForm()
    return render(request, "accounts/register.html", {"form": form})


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    current_template = get_current_template(request.user)
    return render(request, "accounts/profile.html", {"current_template": current_template})
