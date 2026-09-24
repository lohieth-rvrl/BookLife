from django.test import TestCase, Client
from django.core.management import call_command
from django.contrib.auth.models import Group, Permission
from accounts.models import User
from django.contrib.contenttypes.models import ContentType
from books.models import Book
from django.urls import reverse
# from django.contrib.auth import get_user_model

# User = get_user_model()
class CreateAdminCommandTest(TestCase):

    def test_admin_user_created(self):
        call_command("group_setup")

        self.assertFalse(User.objects.filter(email="admin@gmail.com").exists())

        call_command("admin_setup")

        admin = User.objects.get(email="admin@gmail.com")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.groups.filter(name="ADMIN").exists())

    def test_groups_created(self):
        call_command("group_setup")

        self.assertTrue(Group.objects.filter(name="ADMIN").exists())
        self.assertTrue(Group.objects.filter(name="LIBRARIAN").exists())
        self.assertTrue(Group.objects.filter(name="MEMBER").exists())

class AuthViewsTest(TestCase):

    def setUp(self):
        self.client = Client()

        self.member_group, _ = Group.objects.get_or_create(name="MEMBER")

        self.register_url = reverse("accounts:register")
        self.login_url = reverse("accounts:login")
        self.logout_url = reverse("accounts:logout")

        self.user = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "test@123",
            "confirm_password": "test@123"
        }

    def test_register_success(self):
        response = self.client.post(self.register_url, self.user)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="test@gmail.com").exists())


    def test_login_success(self):
        user = User.objects.create_user(
            username="test",
            email="test@gmail.com",
            password="test@123"
        )
        user.groups.add(self.member_group)

        response = self.client.post(self.login_url, {
            "email": "test@gmail.com",
            "password": "test@123"
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("base:base_home"))

    def test_logout_success(self):
        User.objects.create_user(
            username="test",
            email="test@gmail.com",
            password="test@123"
        )

        self.client.post(self.login_url, {
            "email": "test@gmail.com",
            "password": "test@123"
        })

        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:login"))