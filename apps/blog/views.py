from rest_framework import viewsets

from .models import Post, PostCategory
from .permissions import IsStaffAuthor
from .serializers import PostCategorySerializer, PostSerializer


class PostCategoryViewSet(viewsets.ModelViewSet):
    queryset = PostCategory.objects.all()
    serializer_class = PostCategorySerializer
    permission_classes = (IsStaffAuthor,)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('category', 'author').all()
    serializer_class = PostSerializer
    permission_classes = (IsStaffAuthor,)
