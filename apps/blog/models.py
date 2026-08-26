from django.conf import settings
from django.db import models


class PostCategory(models.Model):
    """Dominio propio, separado de catalog.Category: la taxonomía del blog no debe
    acoplarse al catálogo de productos."""

    title = models.CharField(max_length=150)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Post(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/')
    date = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(PostCategory, on_delete=models.PROTECT, related_name='posts')
    # Restricción "solo staff" no existe a nivel de DB (Django no soporta FK
    # condicional); se aplica en la capa de aplicación vía IsStaffAuthor + serializer.
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='posts')

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['category', '-date']),
        ]

    def __str__(self):
        return self.title
