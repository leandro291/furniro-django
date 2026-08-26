from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Snapshot de dirección, copiado en OrderService.create_order — nunca FK ni JSON,
    # así el pedido sobrevive si el usuario edita o borra la Address original.
    address_first_name = models.CharField(max_length=150)
    address_last_name = models.CharField(max_length=150)
    address_street = models.CharField(max_length=255)
    address_city = models.CharField(max_length=100)
    address_province = models.CharField(max_length=100)
    address_phone = models.CharField(max_length=30)
    address_email = models.EmailField()

    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'Order #{self.pk} ({self.status})'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT, related_name='order_items')

    # Snapshot title+precio, copiado en OrderService.create_order — preserva el historial
    # aunque el producto cambie de precio o se descontinúe después.
    title_snapshot = models.CharField(max_length=255)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f'{self.title_snapshot} x{self.quantity}'
