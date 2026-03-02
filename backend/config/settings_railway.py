"""
Railway production settings for GlamConnect.
Extends base settings.py — overrides only what Railway needs.
Set DJANGO_SETTINGS_MODULE=config.settings_railway in Railway env vars.
"""

import os
from .settings import *  # noqa: F401, F403

# ── Security ──────────────────────────────────────────────────────────────────
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)  # noqa: F405

# Railway injects RAILWAY_PUBLIC_DOMAIN automatically
ALLOWED_HOSTS = ['*']

# Railway terminates SSL at the load balancer — never redirect internally
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# ── CORS: allow the Android app to reach the API ─────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ── Database: Railway injects DATABASE_URL automatically ─────────────────────
# Already handled in settings.py via env.db('DATABASE_URL')

# ── Cache: no Redis on Railway free tier — use local memory ──────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ── Celery: run tasks synchronously (no Redis broker needed) ─────────────────
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── Channels: in-memory layer (no Redis needed) ───────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ── Static files: whitenoise serves them directly ────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # noqa: F405
STATICFILES_DIRS = []   # don't look for a 'static/' source dir

# ── Logging: stdout only (Railway captures it) ────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# ── JWT: longer token lifetime for mobile users ───────────────────────────────
from datetime import timedelta
SIMPLE_JWT = {
    **SIMPLE_JWT,  # noqa: F405
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}
