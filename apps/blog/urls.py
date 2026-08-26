from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PostCategoryViewSet, PostViewSet

router = DefaultRouter()
router.register('categories', PostCategoryViewSet, basename='post-category')
router.register('posts', PostViewSet, basename='post')

urlpatterns = [
    path('', include(router.urls)),
]
