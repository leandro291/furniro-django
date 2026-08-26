from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from .filters import ProductFilter
from .models import Category, Product
from .permissions import IsStaffOrReadOnly
from .serializers import CategorySerializer, ProductSerializer, ProductWriteSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsStaffOrReadOnly,)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    permission_classes = (IsStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = ProductFilter
    search_fields = ('title',)

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return ProductWriteSerializer
        return ProductSerializer
