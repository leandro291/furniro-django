from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base = slugify(self.name)
        slug = base
        suffix = 1
        while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            suffix += 1
            slug = f'{base}-{suffix}'
        return slug

    def __str__(self):
        return self.name


class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    rating_rate = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['category', 'stock']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.title
