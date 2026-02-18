"""
Middleware for WebSocket authentication using JWT tokens.
"""

from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import AccessToken, TokenError
from rest_framework_simplejwt.exceptions import InvalidToken
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.

    Token can be passed via:
    1. Query parameter: ws://domain.com/ws/notifications/?token=<jwt_token>
    2. Headers (for clients that support it): Authorization: Bearer <jwt_token>
    """

    async def __call__(self, scope, receive, send):
        """Authenticate the WebSocket connection."""
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        # If no token in query params, try headers
        if not token:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        # Authenticate user
        if token:
            scope['user'] = await self.get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
            logger.warning("WebSocket connection attempt without token")

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        Validate JWT token and return the associated user.

        Args:
            token (str): JWT access token

        Returns:
            User: Authenticated user or AnonymousUser if invalid
        """
        try:
            # Decode and validate the token
            access_token = AccessToken(token)

            # Get user ID from token
            user_id = access_token.get('user_id')

            # Fetch user from database
            user = User.objects.get(id=user_id)

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Inactive user attempted WebSocket connection: {user.email}")
                return AnonymousUser()

            logger.info(f"WebSocket authenticated: {user.email}")
            return user

        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid token in WebSocket connection: {str(e)}")
            return AnonymousUser()

        except User.DoesNotExist:
            logger.warning(f"User not found for token")
            return AnonymousUser()

        except Exception as e:
            logger.error(f"Error authenticating WebSocket: {str(e)}")
            return AnonymousUser()


def JWTAuthMiddlewareStack(inner):
    """
    Convenience function to wrap the WebSocket application with JWT auth middleware.

    Usage in routing.py:
        application = JWTAuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    """
    return JWTAuthMiddleware(inner)
