from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL

class Book(models.Model):

    category_choices = (
        ("Fiction", "Fiction"),
        ("Non-Fiction", "Non-Fiction"),
        ("Science", "Science"),
        ("History", "History"),
        ("Biography", "Biography"),
        ("Children", "Children"),
        ("Fantasy", "Fantasy"),
        ("Mystery", "Mystery"), 
    )

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True)
    category = models.CharField(max_length=100, choices=category_choices)
    image = models.ImageField(upload_to="book_images/", null=True, blank=True)

    total_copies = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.title
    
    def is_held_by_user(self, user):
        return self.reservations.filter(user=user, status="ACTIVE").exclude(expires_at__lt=timezone.now()).exists()
    
    
class Reservation(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("EXPIRED", "Expired"),
        ("COMPLETED", "Completed"),
        ("BORROWED", "Borrowed"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reservations")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    is_expired = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "book"],
                condition=models.Q(status="ACTIVE"),
                name="unique_active_reservation_per_user"
            )
        ]

    # def change_status(self):
    #     if timezone.now() > self.expires_at and not self.status == "COMPLETED":
    #         self.status = "EXPIRED"
    #         self.save()
    #         return self.status
    #     return self.status

    def is_expired(self):
        if timezone.now() > self.expires_at and not self.status == "COMPLETED" and not self.status == "BORROWED":
            self.status = "EXPIRED"
            self.save()
            return self.status
        return self.status
    
    # def make_completed(self):
    #     self.status = "COMPLETED"
    #     self.save()
    #     return self.status
    
    def expires_in(self):
        if self.status == "EXPIRED" and self.status == 'COMPLETED':
            return 0
        else:
            return f'{int((self.expires_at - timezone.now()).total_seconds() // 60)} mins'
        
class Borrow(models.Model):
    STATUS_CHOICES = (
        ("BORROWED", "Borrowed"),
        ("EXPIRED", "Expired"),
        ("RETURNED", "Returned"),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="BORROWED")

    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)

    is_expired = models.BooleanField(default=False)

    class Meta:
        ordering = ["-borrowed_at"]

    def __str__(self):
        return f"{self.book.title}"
    
    def is_expired(self):
        if timezone.now() > self.due_date and not self.status == "RETURNED":
            self.status = "EXPIRED"
            self.save()
            return self.status
        return self.status
    
    def get_due_date(self):
            if self.status == "RETURNED":
                return "No Due"
            else:
                return self.due_date.date()
