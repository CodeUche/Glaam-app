# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec file for GlamConnect standalone .exe
#
# Build with:
#   cd backend
#   pyinstaller standalone.spec --clean --noconfirm
#
# Output: backend/dist/GlamConnect.exe  (~150-200 MB, single file)

import os
import glob
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── Data files Django needs at runtime ──────────────────────────────────────
datas = []

# Django's own templates (admin panel, auth views, etc.)
datas += collect_data_files('django', include_py_files=False)

# DRF's browsable-API templates
datas += collect_data_files('rest_framework', include_py_files=False)

# Channels assets
datas += collect_data_files('channels', include_py_files=False)

# Whitenoise
datas += collect_data_files('whitenoise', include_py_files=False)

# ── Include all local source as data (models, migrations, templates, etc.) ──
# PyInstaller analyses imports statically, but Django discovers apps and
# migrations at runtime via the file system, so we must include the raw
# source as data alongside the compiled bytecode.
LOCAL_DIRS = ['apps', 'config']
for d in LOCAL_DIRS:
    if os.path.isdir(d):
        datas.append((d, d))

# Project-level templates directory (if it exists)
if os.path.isdir('templates'):
    datas.append(('templates', 'templates'))

# ── Hidden imports ───────────────────────────────────────────────────────────
# PyInstaller cannot see dynamic imports; list them explicitly.
hiddenimports = [
    # ── Django internals ───────────────────────────────────────────────────
    'django.contrib.admin',
    'django.contrib.admin.apps',
    'django.contrib.auth',
    'django.contrib.auth.hashers',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sessions.backends.db',
    'django.contrib.messages',
    'django.contrib.messages.storage.fallback',
    'django.contrib.staticfiles',
    'django.core.management.commands.migrate',
    'django.core.management.commands.collectstatic',
    'django.template.loaders.app_directories',
    'django.template.loaders.filesystem',
    'django.template.context_processors',
    'django.middleware.security',
    'django.middleware.common',
    'django.middleware.csrf',
    'django.middleware.clickjacking',

    # ── Third-party ────────────────────────────────────────────────────────
    'rest_framework',
    'rest_framework.authentication',
    'rest_framework.permissions',
    'rest_framework.renderers',
    'rest_framework.parsers',
    'rest_framework.filters',
    'rest_framework.pagination',
    'rest_framework.response',
    'rest_framework.exceptions',
    'rest_framework.fields',
    'rest_framework.serializers',
    'rest_framework.viewsets',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.authentication',
    'rest_framework_simplejwt.tokens',
    'rest_framework_simplejwt.views',
    'rest_framework_simplejwt.serializers',
    'corsheaders',
    'corsheaders.middleware',
    'django_filters',
    'django_filters.rest_framework',
    'channels',
    'channels.layers',
    'channels.generic.websocket',
    'channels.auth',
    'cloudinary',
    'cloudinary.models',
    'cloudinary.uploader',
    'cloudinary.api',
    'whitenoise',
    'whitenoise.middleware',
    'PIL',
    'PIL.Image',

    # ── Local apps ─────────────────────────────────────────────────────────
    'apps',
    'apps.users',
    'apps.users.models',
    'apps.users.views',
    'apps.users.serializers',
    'apps.users.signals',
    'apps.users.tasks',
    'apps.users.utils',
    'apps.users.admin',
    'apps.users.exceptions',
    'apps.users.urls',
    'apps.profiles',
    'apps.profiles.models',
    'apps.profiles.views',
    'apps.profiles.serializers',
    'apps.profiles.admin',
    'apps.profiles.urls',
    'apps.services',
    'apps.services.models',
    'apps.services.views',
    'apps.services.serializers',
    'apps.services.admin',
    'apps.services.urls',
    'apps.bookings',
    'apps.bookings.models',
    'apps.bookings.views',
    'apps.bookings.serializers',
    'apps.bookings.signals',
    'apps.bookings.tasks',
    'apps.bookings.filters',
    'apps.bookings.admin',
    'apps.bookings.urls',
    'apps.reviews',
    'apps.reviews.models',
    'apps.reviews.views',
    'apps.reviews.serializers',
    'apps.reviews.signals',
    'apps.reviews.tasks',
    'apps.reviews.admin',
    'apps.reviews.urls',
    'apps.notifications',
    'apps.notifications.models',
    'apps.notifications.views',
    'apps.notifications.serializers',
    'apps.notifications.signals',
    'apps.notifications.tasks',
    'apps.notifications.urls',
    'apps.payments',
    'apps.payments.models',
    'apps.payments.views',
    'apps.payments.serializers',
    'apps.payments.urls',
    'config.urls',
    'config.wsgi',
    'config.asgi',
    'config.settings_standalone',
]

# Auto-add all migration modules so Django can find them at runtime
for mig in glob.glob('apps/*/migrations/*.py'):
    module = mig.replace(os.sep, '.').replace('/', '.').replace('.py', '')
    hiddenimports.append(module)

# ── Analysis ─────────────────────────────────────────────────────────────────
a = Analysis(
    ['standalone_server.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # GUI toolkits not needed
        'wx',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',

        # Heavy scientific libs not used
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',

        # Dev / debug tools
        'IPython',
        'ipython',
        'debugpy',
        'pydevd',
        'django_debug_toolbar',
        'debug_toolbar',

        # PostgreSQL drivers (SQLite is used instead)
        'psycopg2',
        'psycopg2cffi',
        'psycopg2._psycopg',

        # Redis / Celery / async workers (not needed in standalone)
        # config/__init__.py handles missing celery gracefully via try/except
        'celery',
        'kombu',
        'redis',
        'django_redis',
        'channels_redis',
        'daphne',

        # Cloud storage (using local files)
        'boto3',
        'botocore',
        'django_storages',
        's3transfer',

        # WSGI servers (using wsgiref)
        'gunicorn',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GlamConnect',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # Compress with UPX if available (reduces size ~30%)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,       # Show terminal so users can see server status
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,          # Replace with 'icon.ico' if you have one
)
