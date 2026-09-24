from django.contrib import admin
from .models import Book, Reservation, Borrow

admin.site.register(Book)
admin.site.register(Reservation)
admin.site.register(Borrow)