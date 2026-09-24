from django.core.management.base import BaseCommand
from base.tasks import send_expire_reservations


class Command(BaseCommand):
    help = "Command to expire the reservations"

    def handle(self, *args, **options):
        send_expire_reservations()
        self.stdout.write(self.style.SUCCESS("Expire reservation Cmd done"))