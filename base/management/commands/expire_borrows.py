from django.core.management.base import BaseCommand
from base.tasks import send_expire_borrows

class Command(BaseCommand):
    help = "Command to expire the borrows"

    def handle(self, *args, **options):
        send_expire_borrows()
        self.stdout.write(self.style.SUCCESS("Expire borrow Cmd done"))

    