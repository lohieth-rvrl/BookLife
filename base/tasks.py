from datetime import timedelta
from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now

from books.models import Reservation, Borrow

@shared_task
def send_email_task(subject, message, recipient):
    send_mail(
        subject,
        message,
        None,
        [recipient],
        fail_silently=False
    )

@shared_task
def send_expire_reservations():
    expired = Reservation.objects.filter(
        expires_at__lt=now(),
        status="ACTIVE"
    )

    for r in expired:
        r.book.available_copies += 1
        r.book.save(update_fields=["available_copies"])

        r.status = "EXPIRED"
        r.save(update_fields=["status"])

        # run celery cmd to send mail
        send_email_task.delay(
            "Reservation Expired",
            f"Your reservation for {r.book.title} has expired.",
            r.user.email
        )

    return expired.count()

@shared_task
def send_due_date_reminders():
    today = now().date()

    borrows = Borrow.objects.filter(
        due_date__date=today,
        status="BORROWED"
    )

    for b in borrows:
        # run celery cmd to send mail
        send_email_task.delay(
            "Due Date Reminder",
            f"{b.book.title} is due today.",
            b.user.email
        )

@shared_task
def send_expire_borrows():
    borrow = Borrow.objects.filter(
        due_date__lt=now(),
        status="BORROWED"
    )

    for b in borrow:
        b.status = "EXPIRED"

        b.save(update_fields={"status"})

        # run celery cmd to send mail
        send_email_task.delay(
            "BORROW has been Expired",
            f"Return {b.book.title} book immediately.",
            b.user.email
        )