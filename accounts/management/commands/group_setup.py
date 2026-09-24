from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import User
from books.models import Book, Reservation, Borrow

class Command(BaseCommand):
    help = "Create default groups and assign permissions"

    def handle(self, *args, **options):
        groups_permissions = {
            "ADMIN": "all",
            "LIBRARIAN": [
                "add_book",
                "change_book",
                "delete_book",
                "view_book",

                "add_reservation",
                "change_reservation",
                "delete_reservation",
                "view_reservation",

                "add_borrow",
                "change_borrow",
                "delete_borrow",
                "view_borrow",
            ],

            "MEMBER": [
                "view_book",

                "add_reservation",
                "change_reservation",

                "add_borrow",
                "change_borrow",
            ]
        }

        for group_name, perms in groups_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(self.style.SUCCESS(f"Group created: {group_name}"))
            else:
                self.stdout.write(f"Group exists: {group_name}")

            if perms == "all":
                all_perms = Permission.objects.all()
                group.permissions.set(all_perms)
            else:
                content_type_book = ContentType.objects.get_for_model(Book)
                content_type_reservation = ContentType.objects.get_for_model(Reservation)
                content_type_borrow = ContentType.objects.get_for_model(Borrow)
                permissions = Permission.objects.filter(
                    codename__in=perms,
                    content_type__in=[content_type_book, content_type_reservation, content_type_borrow]
                )
                group.permissions.set(permissions)

            self.stdout.write(self.style.SUCCESS(f"Permissions assigned for group: {group_name}"))
        self.stdout.write(self.style.SUCCESS("Group setup completed"))
