"""
Serializers for user authentication and management.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken as SimpleJWTRefreshToken
from .models import User, UserRole


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Validates password and creates user account.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'role'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs

    def validate_role(self, value):
        """Ensure users can only register as client or artist."""
        if value not in [UserRole.CLIENT, UserRole.ARTIST]:
            raise serializers.ValidationError(
                "Invalid role. Only 'client' or 'artist' allowed during registration."
            )
        return value

    def create(self, validated_data):
        """Create and return new user."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Authenticates user and returns JWT tokens.
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Authenticate user credentials."""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )

            if user.deleted_at:
                raise serializers.ValidationError(
                    'User account has been deleted.',
                    code='authorization'
                )

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code='authorization'
            )


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """

    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.full_name

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'created_at']


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """

    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs

    def validate_old_password(self, value):
        """Verify old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting password reset.
    """

    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset.
    """

    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs


class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer for refreshing access token.
    """

    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        """Validate refresh token."""
        refresh = SimpleJWTRefreshToken(attrs['refresh'])
        attrs['access'] = str(refresh.access_token)
        return attrs
