"""
GlamConnect — Standalone Server Entry Point

This script:
  1. Patches PostgreSQL-only fields so they work with SQLite
  2. Points Django at settings_standalone.py
  3. Runs database migrations automatically
  4. Seeds demo accounts on first run
  5. Serves the API on http://127.0.0.1:8765 using Python's built-in wsgiref

Run directly:
    py standalone_server.py

Or as a PyInstaller .exe (built with standalone.spec):
    GlamConnect.exe
"""

import os
import sys
import types
import socket
import traceback

# When built with console=False, PyInstaller sets sys.stdout/stderr to None.
# Any print() or Django management command output would crash immediately.
# Redirect to devnull so the app runs silently without errors.
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')


# ── Step 1: Path resolution ────────────────────────────────────────────────

def _resolve_dirs():
    """
    Return (app_dir, data_dir).

    app_dir  — where the Python source / bundled code lives (sys._MEIPASS when frozen)
    data_dir — where the SQLite DB, media, and logs are written.
               When frozen: %LOCALAPPDATA%\\GlamConnect  (writable even from Program Files)
               When running as script: same directory as this file
    """
    if getattr(sys, 'frozen', False):
        app_dir = sys._MEIPASS
        local_app = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
        data_dir = os.path.join(local_app, 'GlamConnect')
        os.makedirs(data_dir, exist_ok=True)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = app_dir

    return app_dir, data_dir


# ── Step 2: Monkey-patch PostgreSQL-only fields before Django loads ─────────

def _patch_incompatible_fields():
    """
    Replace fields that require PostgreSQL with SQLite-compatible equivalents.
    Must run before any Django model or migration is imported.
    """
    from django.db import models as _dm

    # ── ArrayField → JSONField ─────────────────────────────────────────────
    class _ArrayField(_dm.JSONField):
        """SQLite-compatible drop-in for django.contrib.postgres.fields.ArrayField."""
        def __init__(self, base_field=None, size=None, **kwargs):
            kwargs.setdefault('default', list)
            super().__init__(**kwargs)

        def formfield(self, **kwargs):
            return super().formfield(**kwargs)

    _fake_pg_fields = types.ModuleType('django.contrib.postgres.fields')
    _fake_pg_fields.ArrayField = _ArrayField
    _fake_pg_fields.HStoreField = _dm.JSONField
    _fake_pg_fields.IntegerArrayField = _ArrayField
    # DRF's ModelSerializer.serializer_field_mapping accesses this at class-definition
    # time. Django 4+ removed it (replaced by models.JSONField) but DRF still references it.
    _fake_pg_fields.JSONField = _dm.JSONField

    _fake_pg = types.ModuleType('django.contrib.postgres')
    _fake_pg.fields = _fake_pg_fields

    sys.modules.setdefault('django.contrib.postgres', _fake_pg)
    sys.modules['django.contrib.postgres.fields'] = _fake_pg_fields

    # ── CloudinaryField → ImageField ───────────────────────────────────────
    try:
        import cloudinary.models as _cm

        class _LocalImageField(_dm.ImageField):
            """ImageField drop-in for CloudinaryField when running standalone."""
            def __init__(self, *args, **kwargs):
                for key in ('type', 'resource_type', 'folder', 'use_filename',
                            'unique_filename', 'overwrite', 'access_mode'):
                    kwargs.pop(key, None)
                super().__init__(*args, **kwargs)

        _cm.CloudinaryField = _LocalImageField
    except Exception:
        pass


# ── Step 3: Celery stub so task files load without Celery installed ─────────

def _patch_celery():
    """
    Inject a minimal fake 'celery' module so that every
    `from celery import shared_task` in the codebase succeeds and tasks
    execute synchronously in the same process.
    """
    try:
        import celery  # Already installed — nothing to do.
        return
    except ImportError:
        pass

    class _FakeTaskSelf:
        """Passed as 'self' when bind=True; retry just re-raises."""
        def retry(self, exc=None, countdown=0, **kwargs):
            if exc:
                raise exc
            raise RuntimeError('Task retry is not available in standalone mode.')

    def _shared_task(func=None, bind=False, **kwargs):
        """
        Drop-in for @shared_task and @shared_task(bind=True, ...).
        Tasks run synchronously; .delay() and .apply_async() work too.
        """
        def decorator(f):
            if bind:
                def wrapper(*args, **kw):
                    return f(_FakeTaskSelf(), *args, **kw)
                wrapper.__name__ = f.__name__
                wrapper.__module__ = f.__module__
            else:
                wrapper = f

            # Support task.delay(...) and task.apply_async(args, kwargs)
            wrapper.delay = wrapper
            wrapper.apply_async = lambda a=(), k={}: wrapper(*a, **k)
            return wrapper

        if func is not None:
            # Used as @shared_task without parentheses
            return decorator(func)
        # Used as @shared_task(...) with parentheses
        return decorator

    _fake_celery = types.ModuleType('celery')
    _fake_celery.shared_task = _shared_task

    # Stub out celery submodules that any app might import
    for _sub in ('app', 'utils', 'utils.log', 'schedules', 'beat', 'result'):
        _m = types.ModuleType(f'celery.{_sub}')
        sys.modules[f'celery.{_sub}'] = _m

    sys.modules['celery'] = _fake_celery


# ── Step 4: Error logging helper ───────────────────────────────────────────

def _fatal_error(data_dir, exc):
    """Write a crash report and show a dialog so the user knows what happened."""
    import datetime
    log_path = os.path.join(data_dir, 'glamconnect_error.log')
    try:
        with open(log_path, 'w') as f:
            f.write(f"GlamConnect crash report — {datetime.datetime.now()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(traceback.format_exc())
            f.write("\n\nsys.path:\n")
            for p in sys.path:
                f.write(f"  {p}\n")
            f.write("\nsys.modules (django*):\n")
            for k in sorted(sys.modules):
                if 'django' in k or 'apps' in k or 'config' in k:
                    f.write(f"  {k}\n")
    except Exception:
        pass

    # Show a dialog box so the user is not left wondering why nothing happened.
    try:
        import ctypes
        msg = (
            f"GlamConnect could not start.\n\n"
            f"Error: {exc}\n\n"
            f"A detailed error report has been saved to:\n{log_path}\n\n"
            f"Please send that file to support."
        )
        ctypes.windll.user32.MessageBoxW(
            0, msg, "GlamConnect — Startup Error", 0x10  # MB_ICONERROR
        )
    except Exception:
        pass


# ── Step 4: Main entry point ───────────────────────────────────────────────

def main():
    app_dir, data_dir = _resolve_dirs()

    # Add app_dir to sys.path so Django can find apps/, config/, etc.
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    # Patch BEFORE setting DJANGO_SETTINGS_MODULE.
    _patch_incompatible_fields()
    _patch_celery()

    # Tell settings_standalone.py where to read/write files.
    os.environ['GLAMCONNECT_APP_DIR'] = app_dir
    os.environ['GLAMCONNECT_DATA_DIR'] = data_dir
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_standalone'

    # Create runtime directories.
    from pathlib import Path
    for folder in ('media', 'staticfiles', 'logs'):
        (Path(data_dir) / folder).mkdir(parents=True, exist_ok=True)

    # Setup Django app registry FIRST (required before any management commands).
    import django
    django.setup()

    # After django.setup() the real django.contrib module is loaded, but our
    # sys.modules patch does NOT automatically set .postgres on that module object.
    # Migration files do `import django.contrib.postgres.fields` then access the
    # field via attribute traversal (django.contrib.postgres.fields.ArrayField),
    # which fails with AttributeError unless we wire up the attribute manually.
    try:
        import django.contrib as _dc
        _dc.postgres = sys.modules['django.contrib.postgres']
    except Exception:
        pass

    # Run migrations.
    print('\n[GlamConnect] Initialising database...')
    from django.core.management import call_command
    call_command('migrate', '--noinput', verbosity=1)

    _seed_demo_data()

    # Collect static files (admin CSS, DRF styles) — failure is non-fatal.
    try:
        call_command('collectstatic', '--noinput', verbosity=0)
    except Exception as e:
        print(f'[WARN] collectstatic skipped: {e}')

    # Find a free port.
    port = _find_free_port(8765)
    # Bind to all interfaces so phones on the same WiFi can connect.
    host = '0.0.0.0'
    local_url = f'http://127.0.0.1:{port}'

    # Get the local network IP so the user can share it with their phone.
    network_url = None
    try:
        import socket as _sock
        with _sock.socket(_sock.AF_INET, _sock.SOCK_DGRAM) as _s:
            _s.connect(('8.8.8.8', 80))
            _network_ip = _s.getsockname()[0]
        network_url = f'http://{_network_ip}:{port}'
    except Exception:
        pass

    # ── Start the HTTP server in a background thread ───────────────────────
    import threading
    import time

    from django.core.wsgi import get_wsgi_application
    from wsgiref.simple_server import make_server

    application = get_wsgi_application()
    httpd = make_server(host, port, application)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    # Poll until the server is actually accepting connections (up to 15 s).
    import urllib.request
    for _ in range(30):
        try:
            urllib.request.urlopen(f'{local_url}/api/v1/', timeout=0.5)
            break
        except Exception:
            time.sleep(0.5)

    # ── Open the app in a native desktop window ────────────────────────────
    _open_desktop_window(local_url, network_url, data_dir, httpd)


# ── Desktop window helpers ──────────────────────────────────────────────────

def _make_loading_html(network_url):
    """Return a branded splash-screen HTML shown while the server starts."""
    phone_block = (
        f'<p class="phone">📱 &nbsp;Phone / Tablet: &nbsp;<b>{network_url}</b></p>'
        if network_url else ''
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GlamConnect</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box }}
  body {{
    background: linear-gradient(135deg, #FFF0F7 0%, #FCE4EC 100%);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 100vh;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }}
  .logo {{ font-size: 80px; margin-bottom: 24px;
           animation: pulse 2s ease-in-out infinite; }}
  @keyframes pulse {{
    0%,100% {{ transform: scale(1) }}
    50%     {{ transform: scale(1.07) }}
  }}
  h1   {{ color:#E91E8C; font-size:42px; font-weight:700; margin-bottom:6px }}
  .tag {{ color:#C2185B; font-size:15px; margin-bottom:44px; opacity:.85 }}
  .msg {{ color:#888;   font-size:15px; margin-bottom:20px }}
  .bar {{
    width:260px; height:6px;
    background: rgba(233,30,140,.18);
    border-radius: 3px; overflow: hidden; margin-bottom: 32px;
  }}
  .fill {{
    height:100%; background:#E91E8C; border-radius:3px;
    animation: slide 1.6s ease-in-out infinite;
  }}
  @keyframes slide {{
    0%   {{ margin-left:0;   width:0%  }}
    50%  {{ margin-left:10%; width:70% }}
    100% {{ margin-left:100%; width:0% }}
  }}
  .phone {{
    font-size:13px; color:#AD1457; padding:10px 18px;
    background: rgba(233,30,140,.08); border-radius:8px;
    font-family: monospace;
  }}
</style>
</head>
<body>
  <div class="logo">💄</div>
  <h1>GlamConnect</h1>
  <p class="tag">Makeup Artist Booking Platform</p>
  <p class="msg">Loading, please wait…</p>
  <div class="bar"><div class="fill"></div></div>
  {phone_block}
</body>
</html>"""


def _find_edge():
    """Return the path to msedge.exe, or None if not found."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    # Fallback: check registry
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe",
        )
        p = winreg.QueryValueEx(key, "")[0]
        if os.path.exists(p):
            return p
    except Exception:
        pass
    return None


def _try_edge_app_mode(url, data_dir):
    """
    Open *url* in Edge --app mode (looks like a real desktop app).
    Uses a private Edge profile so it never touches the user's own Edge.
    Returns True and blocks until the window is closed; returns False if Edge
    is not available.
    """
    import subprocess
    edge = _find_edge()
    if not edge:
        return False

    profile_dir = os.path.join(data_dir, 'edge_profile')
    proc = subprocess.Popen([
        edge,
        f'--app={url}',
        f'--user-data-dir={profile_dir}',
        '--window-size=1280,860',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-sync',
        '--disable-background-networking',
    ])
    proc.wait()   # block until the window is closed
    return True


def _open_desktop_window(local_url, network_url, data_dir, httpd):
    """
    Open GlamConnect in a native desktop window.

    Strategy (tries in order):
      1. pywebview  — proper embedded window, no browser involved
      2. Edge --app — Microsoft Edge in app mode (looks native, no address bar)
      3. Default browser — last resort fallback
    """
    import time
    target = local_url + '/admin/'

    # ── 1. pywebview ────────────────────────────────────────────────────────
    try:
        import webview

        loading_html = _make_loading_html(network_url)

        window = webview.create_window(
            'GlamConnect',
            html=loading_html,
            width=1280,
            height=860,
            min_size=(960, 640),
            background_color='#FFF0F7',
        )

        def _navigate(win):
            # Brief pause so the splash is visible
            time.sleep(0.8)
            win.load_url(target)

        webview.start(func=_navigate, args=[window])

        # Window was closed — shut down the server cleanly.
        try:
            httpd.shutdown()
        except Exception:
            pass
        return

    except Exception:
        pass   # pywebview unavailable or failed → try next option

    # ── 2. Edge --app mode ──────────────────────────────────────────────────
    if _try_edge_app_mode(target, data_dir):
        try:
            httpd.shutdown()
        except Exception:
            pass
        return

    # ── 3. Default browser fallback ─────────────────────────────────────────
    import webbrowser
    webbrowser.open(target)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    try:
        httpd.shutdown()
    except Exception:
        pass


# ── Helpers ────────────────────────────────────────────────────────────────

def _find_free_port(start: int = 8000) -> int:
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start


def _seed_demo_data():
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if User.objects.exists():
        return

    print('[GlamConnect] Creating demo accounts...')

    from decimal import Decimal

    User.objects.create_superuser(
        username='admin',
        email='admin@glamconnect.com',
        password='Admin@1234!',
        first_name='Admin',
        last_name='User',
        role='admin',
    )

    artist_user = User.objects.create_user(
        username='sofia_reyes',
        email='artist@glamconnect.com',
        password='Artist@1234!',
        first_name='Sofia',
        last_name='Reyes',
        role='artist',
        is_verified=True,
    )

    User.objects.create_user(
        username='amara_brooks',
        email='client@glamconnect.com',
        password='Client@1234!',
        first_name='Amara',
        last_name='Brooks',
        role='client',
        is_verified=True,
    )

    from apps.profiles.models import MakeupArtistProfile
    from apps.services.models import Service

    profile, _ = MakeupArtistProfile.objects.get_or_create(
        user=artist_user,
        defaults={
            'bio': (
                'Professional makeup artist with 8+ years of experience '
                'in bridal, editorial, and glamour looks.'
            ),
            'hourly_rate': Decimal('150.00'),
            'location': 'New York, NY',
            'is_available': True,
            'specialties': ['bridal', 'glam', 'editorial'],
        },
    )

    Service.objects.bulk_create([
        Service(
            artist=profile,
            name='Bridal Glam Package',
            description='Full bridal makeup including trial and day-of application.',
            price=Decimal('350.00'),
            duration=120,
            category='bridal',
            is_active=True,
        ),
        Service(
            artist=profile,
            name='Evening Glam',
            description='Full glamour look for events and special occasions.',
            price=Decimal('200.00'),
            duration=90,
            category='glam',
            is_active=True,
        ),
        Service(
            artist=profile,
            name='Natural Everyday Look',
            description='Soft, polished makeup for professional or casual settings.',
            price=Decimal('100.00'),
            duration=60,
            category='natural',
            is_active=True,
        ),
    ])

    print('[GlamConnect] Demo accounts created.')


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    _, data_dir = _resolve_dirs()
    try:
        main()
    except Exception as exc:
        _fatal_error(data_dir, exc)
