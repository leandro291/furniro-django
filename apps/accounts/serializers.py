from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Address, User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        read_only_fields = ('id',)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('id', 'first_name', 'last_name', 'street', 'city', 'province', 'phone', 'email')
        read_only_fields = ('id',)
