from django.conf import settings
from django.db import models

class Activities(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(("activity done :"), max_length=200)
    done_at = models.DateTimeField(auto_now_add=True)

