from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Login por email. El resto del comportamiento viene de AbstractUser."""

    email = models.EmailField('email address', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.first_name} {self.last_name} — {self.street}, {self.city}'
