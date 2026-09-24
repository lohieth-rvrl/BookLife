from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.views.generic import TemplateView

from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import RegisterForm, LoginForm
from django.contrib.auth.models import Group

class RegisterView(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, "accounts/register.html", {"form": form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            member_group, _ = Group.objects.get_or_create(name="MEMBER")
            user.groups.add(member_group)

            login(request, user)

            return redirect("base:base_home")
        return render(request, "accounts/register.html", {"form": form})


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, "accounts/login.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)

            return redirect("base:base_home")
        return render(request, "accounts/login.html", {"form": form})

class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect("accounts:login")
    

