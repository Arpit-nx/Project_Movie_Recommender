from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

class Feedback(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()  # Ensure the field exists
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)