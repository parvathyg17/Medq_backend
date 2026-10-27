import uuid
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Address


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'phone', 'password', 'confirm_password', 'role')
        extra_kwargs = {
            'role': {'default': User.Role.CUSTOMER}
        }

    # Map 'name' from incoming request to 'full_name' for compatibility with original React frontend
    name = serializers.CharField(source='full_name', required=False, allow_blank=True)

    def validate(self, attrs):
        confirm_password = self.initial_data.get('confirm_password') or self.initial_data.get('confirmPassword')
        if confirm_password and attrs.get('password') != confirm_password:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password')
        email = validated_data.get('email')
        
        user = User.objects.create(
            username=email,
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='full_name', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'full_name', 'name', 'phone', 'role', 'is_admin', 'is_delivery_person', 'date_joined')
        read_only_fields = ('id', 'email', 'username', 'role', 'date_joined')


class CustomTokenObtainPairSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get('identifier') or attrs.get('email')
        password = attrs.get('password')

        if not identifier or not password:
            raise serializers.ValidationError("Must include both identifier (email/phone) and password.")

        # Support login by email or phone or username
        user = None
        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(phone=identifier).first() or User.objects.filter(username=identifier).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError({"detail": "Invalid email, phone number, or password."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "This user account is inactive."})

        refresh = RefreshToken.for_user(user)

        # Include custom claims
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['name'] = user.full_name or user.username

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'token': str(refresh.access_token),  # Backward compatibility with original React code
            'role': user.role,
            'user': UserProfileSerializer(user).data
        }


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id', 'full_name', 'phone', 'address_line', 'city', 'state',
            'landmark', 'pin_code', 'address_type', 'is_default', 'created_at'
        )
        read_only_fields = ('id', 'created_at')


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("No account found with this email address.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
