from rest_framework import serializers

from .models import Post, PostCategory


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
