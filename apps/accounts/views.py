from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Address
from .permissions import IsOwner
from .serializers import AddressSerializer, UserRegistrationSerializer
from .throttles import LoginRateThrottle


class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)


class LoginView(TokenObtainPairView):
    throttle_classes = (LoginRateThrottle,)


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = (IsAuthenticated, IsOwner)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Address.objects.none()
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
