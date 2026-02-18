"""
WebSocket URL routing for notifications app.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # User notifications WebSocket
    re_path(
        r'ws/notifications/$',
        consumers.NotificationConsumer.as_asgi(),
        name='ws_notifications'
    ),

    # Artist status WebSocket
    re_path(
        r'ws/artist/(?P<artist_id>[0-9a-f-]+)/status/$',
        consumers.ArtistStatusConsumer.as_asgi(),
        name='ws_artist_status'
    ),
]
