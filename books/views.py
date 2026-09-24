from django.shortcuts import get_object_or_404, render

from django.views.generic import TemplateView, View, UpdateView, DeleteView

from django.contrib.auth.mixins import LoginRequiredMixin,PermissionRequiredMixin
from ajax_datatable.views import AjaxDatatableView
# from ajax_datatable.utils import SkipRow
from django.urls import reverse
from django.http import JsonResponse

from django.db import transaction
from datetime import timedelta
from django.utils import timezone

from base.tasks import send_email_task

from .models import Book, Reservation, Borrow
from .forms import CreateBookForm, UpdateBookForm

from base.models import Activities


# BOOK LOGIC VIEWS

class BookView(LoginRequiredMixin, TemplateView):
    template_name = "base/books.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['books'] = Book.objects.all()
        context['create_form'] = CreateBookForm()
        context['update_form'] = UpdateBookForm()
        return context
    
class GridBookView(LoginRequiredMixin, TemplateView):
    template_name = "base/member/gridview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        books = Book.objects.all()

        context["categorys"] = [choice[0] for choice in Book.category_choices]
        cat = self.request.GET.get("cat") or "all"
        # print(cat)
        # print(cat != "all")
        if cat and (cat != "all"):
            context["has_filter"] = f"Result for: "
            context["category"] = cat.upper
            books = books.filter(category=cat)

        context['books'] = books
        return context


class BookCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'books.add_book'

    def post(self, request, *args, **kwargs):
        form = CreateBookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            Activities.objects.create(user=request.user, message="Created a new book")
            return JsonResponse({
                "success": True,
                "message": "Book created successfully."
            })
        else:
            print(form.errors)
            return JsonResponse({
                "success": False,
                "error": form.errors.as_json()
            })
        
class BookUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "books.change_book"

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        data = {
            "title": book.title,
            "author": book.author,
            "isbn": book.isbn,
            "category": book.category,
            "image": book.image.url if book.image else "",
            "total_copies": book.total_copies,
            "available_copies": book.available_copies,
            "is_active": book.is_active,
        }
        return JsonResponse(data)

    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        form = UpdateBookForm(request.POST, request.FILES, instance=book)

        if form.is_valid():
            form.save()
            Activities.objects.create(user=request.user, message="Updated a book")
            return JsonResponse({"success": True})

        return JsonResponse({
            "success": False,
            "errors": form.errors
        }, status=400)


class BookListView(LoginRequiredMixin, AjaxDatatableView):
    model = Book
    title = 'books'
    initial_order = [['title','desc ']]

    column_defs = [
        {"name": "title", "visible": True, "searchable": True},
        {"name": "author", "visible": True, "searchable": True},
        {"name": "isbn", "visible": True, "searchable": True},
        {"name": "total_copies", "visible": True, "searchable": True},
        {"name": "available_copies", "visible": True, "searchable": True},
        {"name": "category", "visible": True, "searchable": False, "orderable": False},
        {"name": "created_at", "visible": True, "searchable": False, "orderable": False},
        {"name": "updated_at", "visible": True, "searchable": False, "orderable": False},
        {"name": "action", "title": "View", "visible": True, "searchable": False, "orderable": False, "placeholder": True},
    ]

    def customize_row(self, row, obj):
        user = self.request.user
        detail_url = reverse("book:view_book", kwargs={"pk": obj.pk})
        delete_url = reverse("book:delete_book", kwargs={"pk": obj.pk})
        # update_url = reverse("book:update_book", kwargs={"pk": obj.pk})
        action_html = ""

        if user.has_perm("books.view_book"):
            action_html += f'<a href="{detail_url}" class="btn btn-primary btn-sm">View</a> '

        if user.has_perm("books.change_book"):
            action_html += f'<button type="button" class="btn btn-secondary btn-sm edit-btn" data-id="{obj.pk}" data-bs-toggle="modal" data-bs-target="#myEditModal">Edit</button> '

        if user.has_perm("books.delete_book"):
            action_html += f'<button href="{delete_url}" class="btn btn-danger btn-sm delete-btn" data-id="{obj.pk}">Delete</button>'

        row["action"] = action_html
        return row
    
class BookDeleteView(LoginRequiredMixin,PermissionRequiredMixin,View):
    permission_required = 'books.delete_book'
    def post(self, request, pk):
        try:
            obj = Book.objects.get(pk=pk)
            obj.delete()
            Activities.objects.create(user=request.user, message="Deleted a book")
            return JsonResponse({'success': True})
        except Book.DoesNotExist:
            return JsonResponse({'success': False})
        
class BookDetailView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'books.view_book'
    template_name = "base/admin/book_detail.html"
    content_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        book = Book.objects.get(pk=pk)
        context['book'] = book
        return context
    

# RESERVATION LOGIC VIEWS
    

class HoldListView(LoginRequiredMixin, TemplateView):
    template_name = "base/reserves.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class HoldBookListView(LoginRequiredMixin, AjaxDatatableView):
    model = Reservation
    title = "holds"
    initial_order = [["reserved_at", "desc"]]

    column_defs = [
        {"name": "book__title", "visible": True, "searchable": True, "title": "Book Title"},
        {"name": "user__username", "visible": True, "searchable": True, "title": "User"},
        {"name": "reserved_at", "visible": True, "searchable": False, "title": "Reserved At"},
        {"name": "status", "visible": True, "searchable": True},
        {"name": "actions", "visible": True, "searchable": False},
        {"name": "expires", "visible": True, "searchable": False},
    ]

    def get_initial_queryset(self, request=None):
        user = self.request.user

        if user.is_superuser or user.has_perm("books.add_book"):
            return Reservation.objects.all()
        return Reservation.objects.all().filter(user=user)


    def customize_row(self, row, obj):
        user = self.request.user

        row["book__title"] = obj.book.title

        row["user__username"] = obj.user.username

        # row["reserved_at"] = str(obj.reserved_at.date()) + " <div class='vr'></div> " + str(obj.reserved_at.hour) + " o' clock"
        row["reserved_at"] = obj.reserved_at.strftime("%Y-%m-%d %H:%M")

        html = ""

        # obj.is_expired()
        # obj.expires_in()

        if obj.status == "ACTIVE":
            html += f'<button type="button" class="btn btn-warning btn-sm return-hold-btn" data-id="{obj.pk}">Return</button> <div class="vr"></div> <button type="button" class="btn btn-primary btn-sm borrow-hold-btn" data-id="{obj.pk}">Borrow</button> <div class="vr"></div> '
            row["status"] = '<span class="badge bg-success">Active</span>'
            row["expires"] = obj.expires_in()
        elif obj.status == "EXPIRED":
            row["status"] = '<span class="badge bg-danger">Expired</span>'
            if not user.has_perm("books.delete_borrow"):
                html += 'No actions'
            # obj.make_completed()
            row["expires"] = '-'
        elif obj.status == "BORROWED":
            row["status"] = '<span class="badge bg-success">Borrowed</span>'
            row["expires"] = '-'
            if not user.has_perm("books.delete_borrow"):
                html += 'No actions'
        else:
            row["status"] = '<span class="badge bg-secondary">Returned</span>'
            row["expires"] = '-'
            if not user.has_perm("books.delete_borrow"):
                html += 'No actions'

        if user.has_perm("books.delete_reservation"):
            html += f'<button type="button" class="btn btn-danger btn-sm delete-hold-btn" data-id="{obj.pk}">Delete</button> '

        row["actions"] = html

        return row
        # row["expires"] = obj.expires_in()

class HoldBookView(LoginRequiredMixin, View):
    def post(self, request, pk):
        with transaction.atomic():
            book = Book.objects.select_for_update().get(pk=pk)
            if Reservation.objects.filter(user=request.user, book=book).exclude(status__in=["COMPLETED", "BORROWED", "EXPIRED"]).exists():
                return JsonResponse({"success": False, "message": "You already reserved this Book"}, status=400)
            
            if Borrow.objects.filter(user=request.user, book=book).exclude(status="RETURNED").exists():
                return JsonResponse({"success": False, "message": "You already Borrowed this Book"}, status=400)
            
            if book.available_copies <= 0:
                return JsonResponse({"success": False, "message": "Book out of stock"}, status=400)

            Reservation.objects.create(
                user=request.user,
                book=book,
                expires_at=timezone.now() + timedelta(hours=2)
            )

            book.available_copies -= 1
            book.save()
            Activities.objects.create(user=request.user, message="Held a book")
            send_email_task.delay(
                "Reservation Confirmed",
                "Your reservation is confirmed.",
                request.user.email
            )


        return JsonResponse({"success": True})
    
class DeleteHoldBook(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "books.delete_reservation"
    model = Reservation
    
    def post(self, request, *args, **kwargs):
        try:
            Activities.objects.create(user=request.user, message="Deleted a hold book")
            return super().post(request, *args, **kwargs)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    
    def get_success_url(self):
        return reverse('base:base_holds')

class HoldToBorrowView(LoginRequiredMixin, View):
    def post(self, request, pk):
        with transaction.atomic():
            reservation = Reservation.objects.select_for_update().get(
                pk=pk,
                user=request.user,
            )

            book = reservation.book

            if Borrow.objects.filter(user=request.user, book=book).exclude(status="RETURNED").exists():
                return JsonResponse({"success": False, "message": "Already borrowed"}, status=400)

            reservation.status = "BORROWED"
            reservation.save(update_fields=["status"])

            Borrow.objects.create(
                user=request.user,
                book=book,
                due_date=timezone.now() + timedelta(minutes=1)
            )
            send_email_task.delay(
                "Book Borrowed from Hold",
                f"You borrowed {book.title} from your hold. Due on {timezone.now() + timedelta(hours=1)}.",
                request.user.email
            )
            Activities.objects.create(user=request.user, message="Converted a hold to borrowed")
            return JsonResponse({"success": True, "message": "Book hold to borrowed successfully."})

class ReturnHoldBook(LoginRequiredMixin, View):
    
    def post(self, request, pk, *args, **kwargs):
        try:
            reservation = Reservation.objects.filter(user=request.user, pk=pk).exclude(status="COMPLETED").first()
            if reservation and reservation.status != "COMPLETED":
                book = reservation.book
                book.available_copies += 1
                book.save(update_fields=["available_copies"])
                reservation.status = "COMPLETED"
                reservation.save(update_fields=["status"])
            Activities.objects.create(user=request.user, message="Returned a hold book")
            return JsonResponse({"success": True, "message": "Book returned successfully."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

class BorrowBookView(LoginRequiredMixin, View):
    def post(self, request, pk):
        with transaction.atomic():
            book = Book.objects.select_for_update().get(pk=pk)

            if Borrow.objects.filter(user=request.user, book=book).exclude(status="RETURNED").exists():
                return JsonResponse({"success": False, "message": "Book is already borrowed"}, status=400)
            
            if Reservation.objects.filter(user=request.user, book=book, status="ACTIVE").exists():
                return JsonResponse({"success": False, "message": "Book is already reserved"}, status=400)

            if book.available_copies <= 0:
                return JsonResponse({"success": False, "message": "Book out of stock"}, status=400)

            borrow = Borrow.objects.create(
                user=request.user,
                book=book,
                due_date=timezone.now() + timedelta(hours=2)
            )
            Activities.objects.create(user=request.user, message="Borrowed a book")
            book.available_copies -= 1
            book.save(update_fields=["available_copies"])
            send_email_task.delay(
                "Book Borrowed",
                f"You borrowed {book.title}. Due on {borrow.due_date}.",
                borrow.user.email
            )

            return JsonResponse({"success": True})

class BorrowListView(LoginRequiredMixin, TemplateView):
    template_name = "base/borrows.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
class BorrowBookListView(LoginRequiredMixin, AjaxDatatableView):
    model = Borrow
    title = "borrows"
    initial_order = [["borrowed_at", "desc"]]

    column_defs = [
        {"name": "book__title", "visible": True, "searchable": True, "title": "Book Title"},
        {"name": "user__username", "visible": True, "searchable": True, "title": "User"},
        {"name": "borrowed_at", "visible": True, "searchable": True, "title": "Borrowed At"}, 
        {"name": "status", "visible": True, "searchable": True},
        {"name": "actions", "visible": True, "searchable": False},
        {"name": "due_date", "visible": True, "searchable": False},
    ]

    def get_initial_queryset(self, request=None):
        user = self.request.user

        if user.is_superuser or user.has_perm("books.add_book"):
            return Borrow.objects.all()
        return Borrow.objects.all().filter(user=user)


    def customize_row(self, row, obj):
        user = self.request.user

        row["book__title"] = obj.book.title

        row["user__username"] = obj.user.username

        row["borrowed_at"] = str(obj.borrowed_at.date())

        html = ""

        # obj.is_expired()
        if obj.status == "EXPIRED" or obj.status == "BORROWED":
            html += f'<button type="button" class="btn btn-warning btn-sm return-borrow-btn" data-id="{obj.pk}">Return</button> <div class="vr"></div> '
            if obj.status == "EXPIRED":
                row["status"] = '<span class="badge bg-danger">Expired</span>'
            else:
                row["status"] = '<span class="badge bg-success">Borrowed</span>'
            row["due_date"] = obj.get_due_date()
        else:
            row["status"] = '<span class="badge bg-secondary">Returned</span>'            
            row["due_date"] = obj.get_due_date()
            if not user.has_perm("books.delete_borrow"):
                html += 'No actions'


        if user.has_perm("books.delete_borrow"):
            html += f'<button type="button" class="btn btn-danger btn-sm delete-borrow-btn" data-id="{obj.pk}">Delete</button> '
        row["actions"] = html

        return row

class DeleteBorrowBook(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "books.delete_borrow"
    model = Borrow
    
    def post(self, request, *args, **kwargs):
        borrow = self.get_object() 
        if not borrow.status == "RETURNED":
            e = "Return the Book First!"
            return JsonResponse({"success": False, "error": str(e)}, status=400)
        Activities.objects.create(user=request.user, message="Deleted a borrow record")
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('base:base_borrows')

class ReturnBorrowBook(LoginRequiredMixin, View):

    def post(self, request, pk):
        qs = Borrow.objects.filter(pk=pk).exclude(status="RETURNED")

        if not request.user.has_perm("books.change_borrow"):
            qs = qs.filter(user=request.user)
        borrow = qs.first()

        if not borrow:
            return JsonResponse(
                {"success": False, "message": "Borrow not found or already returned"},
                status=404
            )

        book = borrow.book
        book.available_copies += 1
        book.save(update_fields=["available_copies"])

        borrow.status = "RETURNED"
        borrow.save(update_fields=["status"])

        Activities.objects.create(
            user=request.user,
            message=f"Returned {borrow.book.title}"
        )

        return JsonResponse(
            {"success": True, "message": "Book returned successfully"}
        )
            