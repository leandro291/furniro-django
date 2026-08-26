from rest_framework import serializers

from .models import Category, Product

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id', 'slug')


class ProductSerializer(serializers.ModelSerializer):
    """Lectura: expone todos los campos, incluidos los de solo-staff."""

    class Meta:
        model = Product
        fields = ('id', 'title', 'description', 'price', 'image', 'category',
                   'rating_rate', 'rating_count', 'stock')


class ProductWriteSerializer(serializers.ModelSerializer):
    """Solo alcanzable por staff (permiso IsStaffOrReadOnly) — incluye rating_rate/rating_count
    porque la decisión de producto es que esos campos son editables por staff."""

    class Meta:
        model = Product
        fields = ('id', 'title', 'description', 'price', 'image', 'category',
                   'rating_rate', 'rating_count', 'stock')
        read_only_fields = ('id',)

    def validate_image(self, value):
        if value.size > MAX_IMAGE_SIZE_BYTES:
            raise serializers.ValidationError('La imagen no puede superar 5MB.')
        return value
