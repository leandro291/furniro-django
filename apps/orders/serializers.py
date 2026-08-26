from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'title_snapshot', 'price_snapshot', 'quantity', 'subtotal')
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """Salida únicamente: status/total/snapshot los controla OrderService, nunca el cliente."""

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'status', 'total', 'created_at', 'items',
            'address_first_name', 'address_last_name', 'address_street',
            'address_city', 'address_province', 'address_phone', 'address_email',
        )
        read_only_fields = fields


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
    """Entrada de checkout: solo dirección + items. Nada de status/total desde el cliente."""

    address_id = serializers.IntegerField()
    items = OrderItemInputSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('El pedido debe tener al menos un ítem.')
        return value
