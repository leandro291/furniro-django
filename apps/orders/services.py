from decimal import Decimal

from django.db import transaction
from django.db.models import F

from apps.accounts.models import Address
from apps.catalog.models import Product

from .models import Order, OrderItem


class InsufficientStockError(Exception):
    pass


class InvalidOrderStateError(Exception):
    pass


class OrderService:
    """Único punto de mutación de Order/OrderItem/Product.stock. Toda operación que toca
    2+ modelos o necesita atomicidad vive acá, nunca en signals ni en las vistas."""

    @staticmethod
    @transaction.atomic
    def create_order(*, user, address_id, items):
        address = Address.objects.get(id=address_id, user=user)

        order = Order.objects.create(
            user=user,
            status=Order.Status.PENDING,
            address_first_name=address.first_name,
            address_last_name=address.last_name,
            address_street=address.street,
            address_city=address.city,
            address_province=address.province,
            address_phone=address.phone,
            address_email=address.email,
            total=Decimal('0'),
        )

        total = Decimal('0')
        for item in items:
            product = Product.objects.select_for_update().get(id=item['product_id'])
            quantity = item['quantity']

            # UPDATE condicional atómico: si otra transacción ya se llevó el stock,
            # esta fila afectada es 0 y falla acá, sin importar el backend de DB.
            updated = Product.objects.filter(id=product.id, stock__gte=quantity).update(
                stock=F('stock') - quantity
            )
            if not updated:
                raise InsufficientStockError(f'Stock insuficiente para "{product.title}".')

            subtotal = product.price * quantity
            OrderItem.objects.create(
                order=order,
                product=product,
                title_snapshot=product.title,
                price_snapshot=product.price,
                quantity=quantity,
                subtotal=subtotal,
            )
            total += subtotal

        order.total = total
        order.save(update_fields=['total'])
        return order

    @staticmethod
    @transaction.atomic
    def mark_as_paid(*, order):
        if order.status != Order.Status.PENDING:
            raise InvalidOrderStateError('Solo un pedido pending puede marcarse como paid.')
        order.status = Order.Status.PAID
        order.save(update_fields=['status'])
        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(*, order, actor):
        if order.status == Order.Status.CANCELLED:
            raise InvalidOrderStateError('El pedido ya está cancelado.')
        if order.status == Order.Status.PAID and not actor.is_staff:
            raise InvalidOrderStateError('Solo staff puede cancelar un pedido ya pagado.')

        for item in order.items.all():
            Product.objects.filter(id=item.product_id).update(stock=F('stock') + item.quantity)

        order.status = Order.Status.CANCELLED
        order.save(update_fields=['status'])
        return order
