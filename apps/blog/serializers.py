from rest_framework import serializers

from .models import Post, PostCategory

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024


class PostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCategory
        fields = ('id', 'title')
        read_only_fields = ('id',)


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('id', 'title', 'description', 'image', 'date', 'category', 'author')
        read_only_fields = ('id', 'date', 'author')

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

    def validate_image(self, value):
        if value.size > MAX_IMAGE_SIZE_BYTES:
            raise serializers.ValidationError('La imagen no puede superar 5MB.')
        return value
