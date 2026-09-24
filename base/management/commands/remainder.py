from django.core.management.base import BaseCommand
from base.tasks import send_due_date_reminders

class Command(BaseCommand):
    help = "Due date remainder"

    def handle(self, *args, **options):
        send_due_date_reminders()
        self.stdout.write(self.style.SUCCESS("Due date remainder mails sent"))