from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from accounts.forms import RegisterForm
from django.shortcuts import redirect
from django.contrib.auth.models import Group

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from books.models import Book, Reservation, Borrow

from .models import Activities

class home(LoginRequiredMixin, TemplateView):
    # permission_required = 'books.view_book'
    template_name = "base/base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        start = self.request.GET.get("start")
        end = self.request.GET.get("end")

        reservations = Reservation.objects.all()
        borrows = Borrow.objects.all()
        activities = Activities.objects.all()

        if start and end:
            reservations = reservations.filter(reserved_at__date__range=[start, end])
            borrows = borrows.filter(borrowed_at__date__range=[start, end])

        context["reservations_per_day"] = (
            reservations
            .annotate(day=TruncDate("reserved_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("-day")
        )
        context["total_reservations"] = (
            reservations.count()
        )

        context["borrows_per_day"] = (
            borrows
            .annotate(day=TruncDate("borrowed_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("-day")
        )
        context["total_borrows"] = (
            borrows.count()
        )

        context["overdue_borrows"] = Borrow.objects.filter(
            due_date__lt=now(),
            status__in=["BORROWED", "EXPIRED"]
        )

        context["book_utilization"] = Book.objects.annotate(
            borrowed=F("total_copies") - F("available_copies")
        )

        totals = Book.objects.aggregate(
            total=Sum("total_copies"),
            available=Sum("available_copies")
        )

        context["total_books"] = totals["total"] or 0
        context["total_available"] = totals["available"] or 0
        context["total_borrowed"] = context["total_books"] - context["total_available"]

        context["activities"] = activities.order_by("-done_at")[:6]
        print(activities)

        return context

class AddLibraianView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or user.groups.filter(name="ADMIN").exists()):
            return render(request, "base/403_forbidden.html")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        form = RegisterForm()
        add = "Libraian"
        return render(request, "base/admin/adduser.html", {"form": form, "member":add})
    
    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            libraian_group, _ = Group.objects.get_or_create(name="LIBRARIAN")
            user.groups.add(libraian_group)

            return redirect("base:base_home")
        return render(request, "base/admin/adduser.html", {"form": form})

class AddMemberView(LoginRequiredMixin, View):

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_superuser or user.groups.filter(name="ADMIN").exists()):
            return render(request, "base/403_forbidden.html")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        form = RegisterForm()
        add = "Member"
        return render(request, "base/admin/adduser.html", {"form": form, "member":add})

    def post(self, request):
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            member_group, _ = Group.objects.get_or_create(name="MEMBER")
            user.groups.add(member_group)

            return redirect("base:base_home")

        return render(request, "base/admin/adduser.html", {"form": form})