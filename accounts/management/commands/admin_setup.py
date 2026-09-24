from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from accounts.models import User

class Command(BaseCommand):
    help = "Create admin user"

    def handle(self, *args, **options):
        if not User.objects.filter(email="admin@gmail.com").exists():
            admin = User.objects.create_superuser(
                email="admin@gmail.com",
                username="admin",
                password="admin@123"
            )

            admin_group = Group.objects.get(name="ADMIN")
            admin.groups.add(admin_group)

            self.stdout.write(self.style.SUCCESS("Admin user created"))
        else:
            self.stdout.write("Admin user already exists")  