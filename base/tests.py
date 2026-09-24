from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import Group
from django.urls import reverse

from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from books.models import Book, Borrow, Reservation

class ExpireBorrowCommandTest(TestCase):
    def test_expire_borrow_command(self):
        user = User.objects.create_user(
            email="test@gmail.com",
            username="test",
            password="test@123"
        )

        book = Book.objects.create(
            title="demo",
            author="demo",
            isbn="1234",
            category="demo",
            total_copies=5,
            available_copies=4
        )

        borrow = Borrow.objects.create(
            user=user,
            book=book,
            due_date=timezone.now() - timedelta(minutes=5),
            status="BORROWED"
        )

        call_command("expire_borrows")

        borrow.refresh_from_db()

        self.assertEqual(borrow.status, "EXPIRED")
    def test_expire_reservation_command(self):
        user = User.objects.create_user(
            email="test@gmail.com",
            username="test",
            password="test@123"
        )

        book = Book.objects.create(
            title="demo",
            author="demo",
            isbn="1234",
            category="demo",
            total_copies=1,
            available_copies=0
        )

        reservation = Reservation.objects.create(
            user=user,
            book=book,
            status="ACTIVE",
            expires_at=timezone.now() - timedelta(minutes=5)
        )

        call_command("expire_reservations")

        reservation.refresh_from_db()
        self.assertEqual(reservation.status, "EXPIRED")

    def test_remainder_cmd(self):
        user = User.objects.create_user(
            email="test@gmail.com",
            username="test",
            password="test@123"
        )

        book = Book.objects.create(
            title="demo",
            author="demo",
            isbn="1234",
            category="demo",
            total_copies=1,
            available_copies=0
        )

        borrow = Borrow.objects.create(
            user=user,
            book=book,
            status="BORROWED",
            due_date=timezone.now() + timedelta(minutes=5)
        )

        call_command("remainder")

        borrow.refresh_from_db()

        self.assertEqual(borrow.status, "BORROWED")

class HomeViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@gmail.com",
            username="test",
            password="test@123"
        )

    def test_home_requires_login(self):
        response = self.client.get(reverse("base:base_home"))
        self.assertEqual(response.status_code, 302)

class AddLibrarianViewTest(TestCase):

    def setUp(self):
        self.admin_group = Group.objects.create(name="ADMIN")

        self.admin = User.objects.create_user(
            email="admin@gmail.com",
            username="admin",
            password="admin123"
        )
        self.admin.groups.add(self.admin_group)
    
    def test_admin_can_create_librarian(self):
        self.client.login(email="admin@gmail.com", password="admin123")

        response = self.client.post(
            reverse("base:add_lib"),
            {
                "email": "lib@gmail.com",
                "username": "lib",
                "password": "lib@123",
                "confirm_password": "lib@123"
            }
        )

        self.assertRedirects(response, reverse("base:base_home"))

        user = User.objects.get(email="lib@gmail.com")
        self.assertTrue(user.groups.filter(name="LIBRARIAN").exists())
    
    def test_admin_can_create_member(self):
        self.client.login(email="admin@gmail.com", password="admin123")

        response = self.client.post(
            reverse("base:add_mem"),
            {
                "email": "demo@gmail.com",
                "username": "demo",
                "password": "demo@123",
                "confirm_password": "demo@123"
            }
        )

        self.assertRedirects(response, reverse("base:base_home"))

        user = User.objects.get(email="demo@gmail.com")
        self.assertTrue(user.groups.filter(name="MEMBER").exists())
