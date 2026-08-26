from django.core.exceptions import ObjectDoesNotExist
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Order
from .permissions import IsOwnerOrStaff
from .serializers import CheckoutSerializer, OrderSerializer
from .services import InsufficientStockError, InvalidOrderStateError, OrderService


class OrderViewSet(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    """Sin update/destroy directo: toda transición de estado pasa por una @action
    respaldada por OrderService, nunca por un PUT/PATCH crudo del cliente."""

    permission_classes = (IsAuthenticated, IsOwnerOrStaff)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        qs = Order.objects.select_related('user').prefetch_related('items__product')
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return CheckoutSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = OrderService.create_order(user=request.user, **serializer.validated_data)
        except ObjectDoesNotExist:
            raise ValidationError({'address_id': 'Dirección inválida o producto inexistente.'})
        except InsufficientStockError as exc:
            raise ValidationError(str(exc))
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            order = OrderService.cancel_order(order=order, actor=request.user)
        except InvalidOrderStateError as exc:
            raise ValidationError(str(exc))
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['patch'], url_path='mark-as-paid', permission_classes=[IsAdminUser])
    def mark_as_paid(self, request, pk=None):
        order = self.get_object()
        try:
            order = OrderService.mark_as_paid(order=order)
        except InvalidOrderStateError as exc:
            raise ValidationError(str(exc))
        return Response(OrderSerializer(order).data)
