"""
Views for user authentication and management.
"""

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import uuid

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from .models import PasswordResetToken, RefreshToken as CustomRefreshToken
from .permissions import IsOwnerOrReadOnly
from .utils import send_verification_email, send_password_reset_email

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint.
    Allows anyone to create a new account.
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email (async via Celery)
        from .tasks import send_verification_email_task
        send_verification_email_task.delay(user.id)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Store refresh token
        CustomRefreshToken.objects.create(
            user=user,
            token=str(refresh),
            expires_at=timezone.now() + timedelta(days=7)
        )

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful. Please check your email to verify your account.'
        }, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    """
    User login endpoint.
    Authenticates user and returns JWT tokens.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Store refresh token
        CustomRefreshToken.objects.create(
            user=user,
            token=str(refresh),
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class UserLogoutView(APIView):
    """
    User logout endpoint.
    Revokes refresh token.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                # Revoke the token
                token = CustomRefreshToken.objects.filter(
                    token=refresh_token,
                    user=request.user,
                    revoked=False
                ).first()
                if token:
                    token.revoke()

            return Response({
                'message': 'Successfully logged out.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid token.'
            }, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user profile.
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """
    Change user password.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Revoke all existing tokens
        CustomRefreshToken.objects.filter(user=user, revoked=False).update(
            revoked=True,
            revoked_at=timezone.now()
        )

        return Response({
            'message': 'Password changed successfully. Please log in again.'
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """
    Request password reset.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.filter(email=email, deleted_at__isnull=True).first()

        if user:
            # Generate reset token
            token = str(uuid.uuid4())
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=timezone.now() + timedelta(hours=24)
            )

            # Send reset email (async via Celery)
            from .tasks import send_password_reset_email_task
            send_password_reset_email_task.delay(user.id, token)

        # Always return success to prevent email enumeration
        return Response({
            'message': 'If an account exists with this email, you will receive password reset instructions.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        # Validate token
        reset_token = PasswordResetToken.objects.filter(
            token=token,
            used=False
        ).first()

        if not reset_token or not reset_token.is_valid:
            return Response({
                'error': 'Invalid or expired token.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Reset password
        user = reset_token.user
        user.set_password(new_password)
        user.save()

        # Mark token as used
        reset_token.used = True
        reset_token.used_at = timezone.now()
        reset_token.save()

        # Revoke all existing tokens
        CustomRefreshToken.objects.filter(user=user, revoked=False).update(
            revoked=True,
            revoked_at=timezone.now()
        )

        return Response({
            'message': 'Password reset successful. Please log in with your new password.'
        }, status=status.HTTP_200_OK)


class EmailVerificationView(APIView):
    """
    Verify user email address using a signed token.
    Accepts both GET (link click) and POST (form submission).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Handle verification via link click (token in query param)."""
        token = request.query_params.get('token')
        return self._verify_token(token)

    def post(self, request):
        """Handle verification via form submission (token in request body)."""
        token = request.data.get('token')
        return self._verify_token(token)

    def _verify_token(self, token):
        """Verify the email token and mark user as verified."""
        if not token:
            return Response(
                {'error': 'Verification token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .utils import verify_email_token
        user_pk = verify_email_token(token)

        if not user_pk:
            return Response(
                {'error': 'Invalid or expired verification token. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(pk=user_pk, deleted_at__isnull=True)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_verified:
            return Response(
                {'message': 'Email is already verified.'},
                status=status.HTTP_200_OK
            )

        user.is_verified = True
        user.save(update_fields=['is_verified'])

        return Response(
            {'message': 'Email verified successfully. You can now log in.'},
            status=status.HTTP_200_OK
        )


class ResendVerificationEmailView(APIView):
    """
    Resend the verification email for the currently authenticated user.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_verified:
            return Response(
                {'message': 'Your email is already verified.'},
                status=status.HTTP_200_OK
            )

        from .tasks import send_verification_email_task
        send_verification_email_task.delay(str(user.id))

        return Response(
            {'message': 'Verification email sent. Please check your inbox.'},
            status=status.HTTP_200_OK
        )
