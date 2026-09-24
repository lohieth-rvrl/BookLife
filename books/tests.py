from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from books.models import Book, Reservation, Borrow
from django.test import Client
from books.forms import CreateBookForm, UpdateBookForm
from django.contrib.auth.models import Group, Permission


User = get_user_model()

class BookViewsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            email="admin@gmail.com",
            password="admin@123"
        )

        perms = Permission.objects.filter(
            codename__in=[
                "add_book",
                "change_book",
                "delete_book",
                "view_book"
            ]
        )
        self.user.user_permissions.set(perms)

        self.client.login(
            email="admin@gmail.com",
            password="admin@123"
        )

        self.book = Book.objects.create(
            title="demo",
            author="demo",
            isbn="1234",
            category="Science",
            total_copies=5,
            available_copies=5,
            is_active=True
        )

    def test_book_create_success(self):
        url = reverse("book:create_book")
        data = {
            "title": "new",
            "author": "new",
            "isbn": "12345",
            "category": "Science",
            "total_copies": 10,
            "available_copies": 10,
            "is_active": True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_book_update_post(self):
        url = reverse("book:update_book", kwargs={"pk": self.book.pk})
        data = {
            "title": "Updated demo",
            "author": "demo",
            "isbn": "1234",
            "category": "Science",
            "total_copies": 7,
            "available_copies": 7,
            "is_active": True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "Updated demo")

    def test_book_delete_success(self):
        url = reverse("book:delete_book", kwargs={"pk": self.book.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())

    def test_book_detail_success(self):
        url = reverse("book:view_book", kwargs={"pk": self.book.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.book.title)


class BookFormTest(TestCase):

    def test_create_form_valid_data(self):
        form_data = {
            'title': 'test',
            'author': 'test',
            'isbn': '123',
            'category': 'Science',
            'total_copies': 5,
            'available_copies': 3
        }
        form = CreateBookForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_create_form_invalid_available_copies(self):
        form_data = {
            'title': 'test',
            'author': 'test',
            'isbn': '123',
            'category': 'Science',
            'total_copies': 5,
            'available_copies': 10
        }
        form = CreateBookForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('available_copies', form.errors)

    def test_update_form_valid_data(self):
        book = Book.objects.create(
            title='Old Book', author='Author', isbn='1111', category='Sci', total_copies=5, available_copies=2
        )
        form_data = {
            'title': 'Updated test',
            'author': 'test',
            'isbn': '123',
            'category': 'Science',
            'total_copies': 5,
            'available_copies': 5,
            'is_active': True
        }
        form = UpdateBookForm(data=form_data, instance=book)
        self.assertTrue(form.is_valid())


class HoldViewsTest(TestCase):

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="user",
            email="user@gmail.com",
            password="user123"
        )

        self.admin = User.objects.create_user(
            username="admin",
            email="admin@gmail.com",
            password="admin123"
        )

        perms = [
            "add_reservation",
            "change_reservation",
            "delete_reservation",
            "add_book"
        ]

        for perm in perms:
            self.admin.user_permissions.add(
                Permission.objects.get(codename=perm)
            )

        self.book = Book.objects.create(
            title="test",
            author="test",
            isbn="123",
            category="Science",
            total_copies=5,
            available_copies=5,
            is_active=True
        )

        self.hold_url = reverse("book:hold_book", args=[self.book.pk])

    def login_user(self):
        self.client.post(
            reverse("accounts:login"),
            {"email": "user@gmail.com", "password": "user123"}
        )

    def login_admin(self):
        self.client.post(
            reverse("accounts:login"),
            {"email": "admin@gmail.com", "password": "admin123"}
        )

    def test_hold_book_success(self):
        self.login_user()
        response = self.client.post(self.hold_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Reservation.objects.filter(user=self.user, book=self.book).exists()
        )

        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 4)

    def test_hold_book_out_of_stock(self):
        self.book.available_copies = 0
        self.book.save()

        self.login_user()
        response = self.client.post(self.hold_url)
        self.assertEqual(response.status_code, 400)

    def test_duplicate_hold_not_allowed(self):
        Reservation.objects.create(
            user=self.user,
            book=self.book,
            expires_at=timezone.now() + timedelta(minutes=1)
        )

        self.login_user()
        response = self.client.post(self.hold_url)
        self.assertEqual(response.status_code, 400)

    def test_hold_to_borrow_success(self):
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book,
            expires_at=timezone.now() + timedelta(minutes=1)
        )

        self.login_user()
        response = self.client.post(
            reverse("book:hold_to_borrow", args=[reservation.pk])
        )

        self.assertEqual(response.status_code, 200)

        reservation.refresh_from_db()
        self.assertEqual(reservation.status, "BORROWED")

        self.assertTrue(
            Borrow.objects.filter(user=self.user, book=self.book).exists()
        )

    def test_return_hold_book(self):
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book,
            expires_at=timezone.now() + timedelta(minutes=1)
        )

        self.book.available_copies = 3
        self.book.save()

        self.login_admin()
        response = self.client.post(
            reverse("book:hold_book", args=[reservation.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_delete_hold_success(self):
        reservation = Reservation.objects.create(
            user=self.user,
            book=self.book,
            status="COMPLETED",
            expires_at=timezone.now()
        )

        self.login_admin()
        response = self.client.post(
            reverse("book:hold_delete", args=[reservation.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Reservation.objects.filter(pk=reservation.pk).exists()
        )


from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from accounts.models import User
from books.models import Book, Borrow
from datetime import timedelta

class BorrowFlowTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.member_group = Group.objects.create(name="MEMBER")
        self.admin_group = Group.objects.create(name="ADMIN")

        self.user = User.objects.create_user(
            email="user@test.com",
            username="user",
            password="pass123"
        )
        self.user.groups.add(self.member_group)

        self.admin = User.objects.create_superuser(
            email="admin@test.com",
            username="admin",
            password="admin123"
        )
        self.admin.groups.add(self.admin_group)

        self.book = Book.objects.create(
            title="Test Book",
            author="Author",
            isbn="1234567890123",
            category="Test",
            total_copies=2,
            available_copies=2
        )

    def test_user_can_borrow_book(self):
        self.client.force_login(self.user)

        url = reverse("book:borrow_book", args=[self.book.pk])
        response = self.client.post(url)

        self.book.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Borrow.objects.count(), 1)
        self.assertEqual(self.book.available_copies, 1)

    def test_user_cannot_borrow_same_book_twice(self):
        self.client.force_login(self.user)

        Borrow.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.now() + timedelta(days=1)
        )

        url = reverse("book:borrow_book", args=[self.book.pk])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Borrow.objects.count(), 1)

    def test_borrow_fails_when_out_of_stock(self):
        self.client.force_login(self.user)

        self.book.available_copies = 0
        self.book.save()

        url = reverse("book:borrow_book", args=[self.book.pk])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Borrow.objects.count(), 0)

    def test_user_can_return_borrowed_book(self):
        self.client.force_login(self.user)

        borrow = Borrow.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.now() + timedelta(days=1)
        )

        self.book.available_copies = 0
        self.book.save()

        perm = Permission.objects.get(codename="change_borrow")
        self.user.user_permissions.add(perm)

        url = reverse("book:borrow_return", args=[borrow.pk])
        response = self.client.post(url)

        borrow.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(borrow.status, "RETURNED")
        self.assertEqual(self.book.available_copies, 1)
