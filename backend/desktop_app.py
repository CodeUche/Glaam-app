"""
GlamConnect Desktop App
=======================
A proper native desktop application — no browser, no web server.
Uses CustomTkinter for the GUI and Django ORM directly for data.

Run:   py desktop_app.py
Build: pyinstaller desktop.spec --clean --noconfirm
"""

import os
import sys
import types
import traceback
from pathlib import Path
from decimal import Decimal
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# ── Brand colours ──────────────────────────────────────────────────────────────
PRIMARY   = "#E91E8C"
PRIMARY_D = "#C2185B"
ACCENT    = "#FF4081"
BG        = "#FBF3F7"
SIDEBAR   = "#3D0026"
SIDEBAR_H = "#5C0038"
SURFACE   = "#FFFFFF"
TEXT      = "#1A1A1A"
TEXT2     = "#757575"
SUCCESS   = "#2E7D32"
WARNING   = "#F57F17"
DANGER    = "#C62828"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")  # we override colours manually


# ── Path resolution ────────────────────────────────────────────────────────────
def _resolve_dirs():
    if getattr(sys, 'frozen', False):
        app_dir  = sys._MEIPASS
        local_app = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
        data_dir = os.path.join(local_app, 'GlamConnect')
        os.makedirs(data_dir, exist_ok=True)
    else:
        app_dir  = os.path.dirname(os.path.abspath(__file__))
        data_dir = app_dir
    return app_dir, data_dir


# ── Django bootstrap ───────────────────────────────────────────────────────────
def _bootstrap_django(app_dir, data_dir):
    """Patch incompatible fields, set up Django, run migrations."""
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    # Patch PostgreSQL-only fields → SQLite equivalents
    from django.db import models as _dm

    class _ArrayField(_dm.JSONField):
        def __init__(self, base_field=None, size=None, **kwargs):
            kwargs.setdefault('default', list)
            super().__init__(**kwargs)

    _pg_fields = types.ModuleType('django.contrib.postgres.fields')
    _pg_fields.ArrayField       = _ArrayField
    _pg_fields.HStoreField      = _dm.JSONField
    _pg_fields.JSONField        = _dm.JSONField
    _pg_fields.IntegerArrayField = _ArrayField
    _pg = types.ModuleType('django.contrib.postgres')
    _pg.fields = _pg_fields
    sys.modules.setdefault('django.contrib.postgres', _pg)
    sys.modules['django.contrib.postgres.fields'] = _pg_fields

    try:
        import cloudinary.models as _cm
        class _LocalImage(_dm.ImageField):
            def __init__(self, *a, **kw):
                for k in ('type','resource_type','folder','use_filename',
                           'unique_filename','overwrite','access_mode'):
                    kw.pop(k, None)
                super().__init__(*a, **kw)
        _cm.CloudinaryField = _LocalImage
    except Exception:
        pass

    # Celery stub
    def _shared_task(func=None, bind=False, **kw):
        def dec(f):
            f.delay = f
            f.apply_async = lambda a=(), k={}: f(*a, **k)
            return f
        return dec(func) if func is not None else dec

    _cel = types.ModuleType('celery')
    _cel.shared_task = _shared_task
    for _sub in ('app','utils','utils.log','schedules','beat','result'):
        sys.modules.setdefault(f'celery.{_sub}', types.ModuleType(f'celery.{_sub}'))
    sys.modules.setdefault('celery', _cel)

    os.environ['GLAMCONNECT_APP_DIR'] = app_dir
    os.environ['GLAMCONNECT_DATA_DIR'] = data_dir
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_standalone'

    for folder in ('media', 'staticfiles', 'logs'):
        Path(data_dir, folder).mkdir(parents=True, exist_ok=True)

    import django
    django.setup()

    try:
        import django.contrib as _dc
        _dc.postgres = sys.modules['django.contrib.postgres']
    except Exception:
        pass

    from django.core.management import call_command
    call_command('migrate', '--noinput', verbosity=0)
    _seed_demo_data()


def _seed_demo_data():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if User.objects.exists():
        return

    User.objects.create_superuser(
        username='admin', email='admin@glamconnect.com',
        password='Admin@1234!', first_name='Admin', last_name='User', role='admin',
    )
    artist = User.objects.create_user(
        username='sofia_reyes', email='artist@glamconnect.com',
        password='Artist@1234!', first_name='Sofia', last_name='Reyes',
        role='artist', is_verified=True,
    )
    User.objects.create_user(
        username='amara_brooks', email='client@glamconnect.com',
        password='Client@1234!', first_name='Amara', last_name='Brooks',
        role='client', is_verified=True,
    )

    from apps.profiles.models import MakeupArtistProfile
    from apps.services.models import Service

    profile, _ = MakeupArtistProfile.objects.get_or_create(
        user=artist,
        defaults=dict(
            bio='Professional makeup artist with 8+ years of experience in bridal, editorial, and glamour looks.',
            hourly_rate=Decimal('150.00'), location='New York, NY',
            is_available=True, specialties=['bridal','glam','editorial'],
        ),
    )
    Service.objects.bulk_create([
        Service(artist=profile, name='Bridal Glam Package',
                description='Full bridal makeup including trial and day-of application.',
                price=Decimal('350.00'), duration=120, category='bridal', is_active=True),
        Service(artist=profile, name='Evening Glam',
                description='Full glamour look for events and special occasions.',
                price=Decimal('200.00'), duration=90, category='glam', is_active=True),
        Service(artist=profile, name='Natural Everyday Look',
                description='Soft, polished makeup for professional or casual settings.',
                price=Decimal('100.00'), duration=60, category='natural', is_active=True),
    ])


# ══════════════════════════════════════════════════════════════════════════════
#  WIDGETS / HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def stat_card(parent, title, value, color=PRIMARY):
    """A small stats card widget."""
    card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12,
                        border_width=1, border_color="#F0DCE8")
    ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=28, weight="bold"),
                 text_color=color).pack(pady=(18, 2))
    ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12),
                 text_color=TEXT2).pack(pady=(0, 16))
    return card


def section_title(parent, text):
    ctk.CTkLabel(parent, text=text,
                 font=ctk.CTkFont(size=18, weight="bold"),
                 text_color=TEXT).pack(anchor="w", pady=(0, 12))


def styled_table(parent, columns, rows, col_widths=None):
    """Build a ttk.Treeview styled to match the app theme."""
    style = ttk.Style()
    style.theme_use("default")
    style.configure("G.Treeview",
                    background=SURFACE, foreground=TEXT,
                    rowheight=36, fieldbackground=SURFACE,
                    font=("Segoe UI", 11))
    style.configure("G.Treeview.Heading",
                    background="#F8E8F2", foreground=PRIMARY_D,
                    font=("Segoe UI", 11, "bold"), relief="flat")
    style.map("G.Treeview", background=[("selected", "#FCE4EC")],
              foreground=[("selected", PRIMARY_D)])

    frame = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color="#F0DCE8")
    frame.pack(fill="both", expand=True)

    sb = ttk.Scrollbar(frame, orient="vertical")
    tree = ttk.Treeview(frame, columns=columns, show="headings",
                        style="G.Treeview", yscrollcommand=sb.set)
    sb.config(command=tree.yview)

    widths = col_widths or {}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=widths.get(col, 150), anchor="w")

    for row in rows:
        tree.insert("", "end", values=row)

    tree.pack(side="left", fill="both", expand=True, padx=4, pady=4)
    sb.pack(side="right", fill="y", pady=4)
    return tree


def _form_field(parent, label, var, show=None, pady_top=16):
    """Helper to render a labelled entry field."""
    ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=13),
                 text_color=TEXT2).pack(anchor="w", padx=24, pady=(pady_top, 4))
    e = ctk.CTkEntry(parent, textvariable=var, height=44,
                     border_color=PRIMARY, font=ctk.CTkFont(size=14),
                     show=show or "")
    e.pack(padx=24, fill="x")
    return e


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

class Sidebar(ctk.CTkFrame):
    ADMIN_ITEMS = [
        ("dashboard", "🏠  Dashboard"),
        ("bookings",  "📅  Bookings"),
        ("artists",   "💄  Artists"),
        ("services",  "✨  Services"),
        ("clients",   "👤  Clients"),
    ]
    CLIENT_ITEMS = [
        ("browse",      "💄  Browse Artists"),
        ("my_bookings", "📅  My Bookings"),
        ("profile",     "👤  My Profile"),
    ]
    ARTIST_ITEMS = [
        ("dashboard",   "🏠  Dashboard"),
        ("my_bookings", "📅  My Bookings"),
        ("profile",     "👤  My Profile"),
        ("services",    "✨  My Services"),
    ]

    @classmethod
    def items_for_role(cls, role):
        if role == 'client':
            return cls.CLIENT_ITEMS
        if role == 'artist':
            return cls.ARTIST_ITEMS
        return cls.ADMIN_ITEMS

    def __init__(self, parent, on_nav, on_logout, user):
        super().__init__(parent, fg_color=SIDEBAR, corner_radius=0, width=220)
        self.grid_propagate(False)
        self.on_nav   = on_nav
        self._buttons = {}
        self._active  = None
        self._build(user, on_logout)

    def _build(self, user, on_logout):
        ctk.CTkLabel(self, text="💄", font=ctk.CTkFont(size=40)).pack(pady=(30, 4))
        ctk.CTkLabel(self, text="GlamConnect",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="white").pack()
        ctk.CTkLabel(self, text="Booking Platform",
                     font=ctk.CTkFont(size=11), text_color="#FFAAD4").pack(pady=(2, 28))

        ctk.CTkFrame(self, height=1, fg_color="#5C0038").pack(fill="x", padx=20)

        for key, label in self.items_for_role(user.role):
            btn = ctk.CTkButton(
                self, text=label, anchor="w",
                font=ctk.CTkFont(size=14),
                height=44, corner_radius=8,
                fg_color="transparent", hover_color=SIDEBAR_H,
                text_color="white",
                command=lambda k=key: self.on_nav(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self._buttons[key] = btn

        ctk.CTkFrame(self, height=1, fg_color="#5C0038").pack(fill="x", padx=20, pady=(20, 0))
        name = user.get_full_name() or user.email
        role = user.get_role_display()
        ctk.CTkLabel(self, text=f"👤  {name}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="white", anchor="w").pack(fill="x", padx=20, pady=(12, 2))
        ctk.CTkLabel(self, text=role, font=ctk.CTkFont(size=11),
                     text_color="#FFAAD4", anchor="w").pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkButton(self, text="Sign Out", height=34, corner_radius=8,
                      fg_color="#5C0038", hover_color=DANGER,
                      font=ctk.CTkFont(size=12), text_color="white",
                      command=on_logout).pack(fill="x", padx=12, pady=(0, 20))

    def set_active(self, key):
        if self._active and self._active in self._buttons:
            self._buttons[self._active].configure(fg_color="transparent")
        if key in self._buttons:
            self._buttons[key].configure(fg_color=SIDEBAR_H)
            self._active = key


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN PAGES
# ══════════════════════════════════════════════════════════════════════════════

class DashboardPage(ctk.CTkScrollableFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self._build(user)

    def _build(self, user):
        section_title(self, f"Welcome back, {user.first_name or 'there'} 👋")

        from django.contrib.auth import get_user_model
        from apps.bookings.models  import Booking
        from apps.profiles.models  import MakeupArtistProfile

        User = get_user_model()
        total_bookings  = Booking.objects.count()
        pending         = Booking.objects.filter(status='pending').count()
        confirmed       = Booking.objects.filter(status='confirmed').count()
        total_artists   = MakeupArtistProfile.objects.filter(is_available=True).count()
        total_clients   = User.objects.filter(role='client').count()

        try:
            from apps.payments.models import Payment
            from django.db.models import Sum
            revenue = Payment.objects.filter(
                status='completed').aggregate(t=Sum('amount'))['t'] or 0
            revenue_str = f"${revenue:,.2f}"
        except Exception:
            revenue_str = "N/A"

        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 24))
        stats_frame.grid_columnconfigure((0,1,2,3), weight=1)

        cards = [
            ("Total Bookings", str(total_bookings), PRIMARY),
            ("Pending",        str(pending),        WARNING),
            ("Active Artists", str(total_artists),  "#1565C0"),
            ("Clients",        str(total_clients),  SUCCESS),
        ]
        for col, (title, val, color) in enumerate(cards):
            c = stat_card(stats_frame, title, val, color)
            c.grid(row=0, column=col, padx=8, sticky="ew")

        section_title(self, "Recent Bookings")

        bookings = Booking.objects.select_related(
            'client', 'service', 'service__artist__user'
        ).order_by('-created_at')[:20]

        rows = []
        for b in bookings:
            client_name = b.client.get_full_name() if hasattr(b, 'client') else "—"
            artist_name = "—"
            svc_name    = "—"
            try:
                artist_name = b.service.artist.user.get_full_name()
                svc_name    = b.service.name
            except Exception:
                pass
            rows.append((
                str(b.id)[:8] + "…",
                client_name,
                artist_name,
                svc_name,
                b.status.capitalize(),
                b.booking_date.strftime("%d %b %Y") if b.booking_date else "—",
            ))

        if rows:
            styled_table(self,
                columns=("ID","Client","Artist","Service","Status","Date"),
                rows=rows,
                col_widths={"ID":90,"Client":150,"Artist":150,"Service":180,"Status":100,"Date":110},
            )
        else:
            ctk.CTkLabel(self, text="No bookings yet.",
                         font=ctk.CTkFont(size=14), text_color=TEXT2).pack(pady=40)


class BookingsPage(ctk.CTkScrollableFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.user = user
        self._build()

    def _build(self):
        section_title(self, "📅  All Bookings")

        from apps.bookings.models import Booking
        bookings = Booking.objects.select_related(
            'client', 'service', 'service__artist__user'
        ).order_by('-created_at')

        rows = []
        for b in bookings:
            try:
                client = b.client.get_full_name() or b.client.email
            except Exception:
                client = "—"
            try:
                artist = b.service.artist.user.get_full_name()
                svc    = b.service.name
                price  = f"${b.service.price}"
            except Exception:
                artist = svc = price = "—"
            rows.append((
                str(b.id)[:8] + "…",
                client, artist, svc, price,
                b.status.capitalize(),
                b.booking_date.strftime("%d %b %Y") if b.booking_date else "—",
            ))

        if rows:
            styled_table(self,
                columns=("ID","Client","Artist","Service","Price","Status","Date"),
                rows=rows,
                col_widths={"ID":90,"Client":150,"Artist":150,"Service":180,
                            "Price":80,"Status":100,"Date":110},
            )
        else:
            ctk.CTkLabel(self, text="No bookings yet.",
                         font=ctk.CTkFont(size=14), text_color=TEXT2).pack(pady=60)


class ArtistsPage(ctk.CTkScrollableFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self._build()

    def _build(self):
        section_title(self, "💄  Makeup Artists")

        from apps.profiles.models import MakeupArtistProfile

        artists = MakeupArtistProfile.objects.select_related('user').all()

        if not artists:
            ctk.CTkLabel(self, text="No artists registered yet.",
                         font=ctk.CTkFont(size=14), text_color=TEXT2).pack(pady=60)
            return

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x")

        for i, artist in enumerate(artists):
            col = i % 2
            row = i // 2
            grid.grid_columnconfigure(col, weight=1)
            self._artist_card(grid, artist).grid(
                row=row, column=col, padx=8, pady=8, sticky="ew"
            )

    def _artist_card(self, parent, artist):
        card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=16,
                            border_width=1, border_color="#F0DCE8")

        name = artist.user.get_full_name() or artist.user.email
        ctk.CTkLabel(card, text=f"💄  {name}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=PRIMARY).pack(anchor="w", padx=20, pady=(20, 4))

        ctk.CTkLabel(card, text=f"📍  {artist.location or 'Location not set'}",
                     font=ctk.CTkFont(size=12), text_color=TEXT2).pack(anchor="w", padx=20)

        ctk.CTkLabel(card, text=f"💰  ${artist.hourly_rate}/hr",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=SUCCESS).pack(anchor="w", padx=20, pady=(4, 4))

        if artist.bio:
            bio = artist.bio[:120] + ("…" if len(artist.bio) > 120 else "")
            ctk.CTkLabel(card, text=bio, wraplength=340,
                         font=ctk.CTkFont(size=11), text_color=TEXT2,
                         justify="left").pack(anchor="w", padx=20, pady=(0, 8))

        specialties = artist.specialties or []
        if specialties:
            tags_frame = ctk.CTkFrame(card, fg_color="transparent")
            tags_frame.pack(anchor="w", padx=20, pady=(0, 8))
            for tag in specialties[:4]:
                ctk.CTkLabel(tags_frame, text=f"  {tag}  ",
                             font=ctk.CTkFont(size=11),
                             fg_color="#FCE4EC", corner_radius=10,
                             text_color=PRIMARY_D).pack(side="left", padx=2)

        avail = "✅  Available" if artist.is_available else "⛔  Unavailable"
        color = SUCCESS if artist.is_available else DANGER
        ctk.CTkLabel(card, text=avail, font=ctk.CTkFont(size=12),
                     text_color=color).pack(anchor="w", padx=20, pady=(0, 20))

        return card


class ServicesPage(ctk.CTkScrollableFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self._build()

    def _build(self):
        section_title(self, "✨  Services")

        from apps.services.models import Service
        services = Service.objects.select_related('artist__user').filter(is_active=True)

        rows = []
        for s in services:
            try:
                artist = s.artist.user.get_full_name()
            except Exception:
                artist = "—"
            rows.append((
                s.name,
                artist,
                s.category.capitalize(),
                f"${s.price}",
                f"{s.duration} min",
                "Active" if s.is_active else "Inactive",
            ))

        if rows:
            styled_table(self,
                columns=("Service","Artist","Category","Price","Duration","Status"),
                rows=rows,
                col_widths={"Service":220,"Artist":160,"Category":120,
                            "Price":90,"Duration":100,"Status":80},
            )
        else:
            ctk.CTkLabel(self, text="No services yet.",
                         font=ctk.CTkFont(size=14), text_color=TEXT2).pack(pady=60)


class ClientsPage(ctk.CTkScrollableFrame):
    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self._build()

    def _build(self):
        section_title(self, "👤  Clients")

        from django.contrib.auth import get_user_model
        from apps.bookings.models import Booking

        User = get_user_model()
        clients = User.objects.filter(role='client').order_by('-created_at')

        rows = []
        for c in clients:
            total = Booking.objects.filter(client=c).count()
            rows.append((
                c.get_full_name() or "—",
                c.email,
                c.phone_number or "—",
                "Verified ✅" if c.is_verified else "Unverified",
                str(total),
                c.created_at.strftime("%d %b %Y"),
            ))

        if rows:
            styled_table(self,
                columns=("Name","Email","Phone","Verified","Bookings","Joined"),
                rows=rows,
                col_widths={"Name":160,"Email":220,"Phone":120,
                            "Verified":100,"Bookings":80,"Joined":110},
            )
        else:
            ctk.CTkLabel(self, text="No clients registered yet.",
                         font=ctk.CTkFont(size=14), text_color=TEXT2).pack(pady=60)


# ══════════════════════════════════════════════════════════════════════════════
#  CLIENT PAGES
# ══════════════════════════════════════════════════════════════════════════════

class BookingDialog(ctk.CTkToplevel):
    """Modal dialog for booking an artist's service."""

    def __init__(self, parent, client_user, artist_profile, on_booked):
        super().__init__(parent)
        self.title(f"Book — {artist_profile.user.get_full_name()}")
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.grab_set()
        self.client_user    = client_user
        self.artist_profile = artist_profile
        self.on_booked      = on_booked
        self._center(parent)
        self._build()

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        self.geometry(f"480x520+{px - 240}+{py - 260}")

    def _build(self):
        from apps.services.models import Service
        services = list(Service.objects.filter(
            artist=self.artist_profile, is_active=True))

        ctk.CTkLabel(self, text="📅  Book Appointment",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY).pack(pady=(24, 4))
        artist_name = self.artist_profile.user.get_full_name()
        ctk.CTkLabel(self, text=f"with {artist_name}",
                     font=ctk.CTkFont(size=13), text_color=TEXT2).pack(pady=(0, 16))

        card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=16,
                            border_width=1, border_color="#F0DCE8")
        card.pack(padx=24, fill="x")

        # Service dropdown
        ctk.CTkLabel(card, text="Select Service", font=ctk.CTkFont(size=13),
                     text_color=TEXT2).pack(anchor="w", padx=24, pady=(20, 4))
        svc_names = [f"{s.name} — ${s.price}" for s in services]
        if not svc_names:
            svc_names = ["No services available"]
        self._svc_var = tk.StringVar(value=svc_names[0])
        ctk.CTkOptionMenu(card, values=svc_names, variable=self._svc_var,
                          fg_color=SURFACE, button_color=PRIMARY,
                          button_hover_color=PRIMARY_D, text_color=TEXT,
                          font=ctk.CTkFont(size=13)).pack(padx=24, fill="x")

        # Date field
        ctk.CTkLabel(card, text="Date (YYYY-MM-DD)", font=ctk.CTkFont(size=13),
                     text_color=TEXT2).pack(anchor="w", padx=24, pady=(16, 4))
        import datetime
        self._date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        ctk.CTkEntry(card, textvariable=self._date_var, height=44,
                     border_color=PRIMARY, font=ctk.CTkFont(size=14)).pack(padx=24, fill="x")

        # Notes field
        ctk.CTkLabel(card, text="Notes (optional)", font=ctk.CTkFont(size=13),
                     text_color=TEXT2).pack(anchor="w", padx=24, pady=(16, 4))
        self._notes = ctk.CTkTextbox(card, height=70, font=ctk.CTkFont(size=13),
                                     border_color=PRIMARY, border_width=1)
        self._notes.pack(padx=24, fill="x", pady=(0, 4))

        self._err = ctk.CTkLabel(card, text="", text_color=DANGER,
                                 font=ctk.CTkFont(size=12))
        self._err.pack(pady=(4, 0))

        ctk.CTkButton(card, text="Confirm Booking", height=48,
                      fg_color=PRIMARY, hover_color=PRIMARY_D,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      corner_radius=24,
                      command=lambda: self._confirm(services)).pack(
            padx=24, pady=(12, 24), fill="x")

    def _confirm(self, services):
        import datetime
        from apps.bookings.models import Booking

        svc_label = self._svc_var.get()
        # Match selected label back to service
        chosen_svc = None
        for s in services:
            if svc_label.startswith(s.name):
                chosen_svc = s
                break

        if chosen_svc is None:
            self._err.configure(text="No service selected.")
            return

        date_str = self._date_var.get().strip()
        try:
            booking_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            self._err.configure(text="Invalid date. Use YYYY-MM-DD format.")
            return

        if booking_date < datetime.date.today():
            self._err.configure(text="Please choose a future date.")
            return

        notes = self._notes.get("1.0", "end").strip()

        try:
            Booking.objects.create(
                client=self.client_user,
                service=chosen_svc,
                booking_date=booking_date,
                status='pending',
                notes=notes,
            )
        except Exception as exc:
            self._err.configure(text=f"Error: {exc}")
            return

        self.destroy()
        self.on_booked()


class BrowseArtistsPage(ctk.CTkScrollableFrame):
    """Client view: browse artists and book a service."""

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.user = user
        self._parent = parent
        self._build()

    def _build(self):
        section_title(self, "💄  Browse Artists")

        from apps.profiles.models import MakeupArtistProfile
        artists = MakeupArtistProfile.objects.select_related('user').filter(is_available=True)

        if not artists:
            ctk.CTkLabel(self, text="No artists available right now. Check back soon!",
                         font=ctk.CTkFont(size=14), text_color=TEXT2).pack(pady=60)
            return

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x")

        for i, artist in enumerate(artists):
            col = i % 2
            row = i // 2
            grid.grid_columnconfigure(col, weight=1)
            self._artist_card(grid, artist).grid(
                row=row, column=col, padx=8, pady=8, sticky="ew"
            )

    def _artist_card(self, parent, artist):
        card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=16,
                            border_width=1, border_color="#F0DCE8")

        name = artist.user.get_full_name() or artist.user.email
        ctk.CTkLabel(card, text=f"💄  {name}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=PRIMARY).pack(anchor="w", padx=20, pady=(20, 4))

        ctk.CTkLabel(card, text=f"📍  {artist.location or 'Location not set'}",
                     font=ctk.CTkFont(size=12), text_color=TEXT2).pack(anchor="w", padx=20)

        ctk.CTkLabel(card, text=f"💰  ${artist.hourly_rate}/hr",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=SUCCESS).pack(anchor="w", padx=20, pady=(4, 4))

        if artist.bio:
            bio = artist.bio[:120] + ("…" if len(artist.bio) > 120 else "")
            ctk.CTkLabel(card, text=bio, wraplength=340,
                         font=ctk.CTkFont(size=11), text_color=TEXT2,
                         justify="left").pack(anchor="w", padx=20, pady=(0, 8))

        specialties = artist.specialties or []
        if specialties:
            tags_frame = ctk.CTkFrame(card, fg_color="transparent")
            tags_frame.pack(anchor="w", padx=20, pady=(0, 8))
            for tag in specialties[:4]:
                ctk.CTkLabel(tags_frame, text=f"  {tag}  ",
                             font=ctk.CTkFont(size=11),
                             fg_color="#FCE4EC", corner_radius=10,
                             text_color=PRIMARY_D).pack(side="left", padx=2)

        from apps.services.models import Service
        svc_count = Service.objects.filter(artist=artist, is_active=True).count()
        ctk.CTkLabel(card, text=f"✨  {svc_count} service{'s' if svc_count != 1 else ''} available",
                     font=ctk.CTkFont(size=12), text_color=TEXT2).pack(anchor="w", padx=20)

        ctk.CTkButton(card, text="Book Now", height=40,
                      fg_color=PRIMARY, hover_color=PRIMARY_D,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=20,
                      command=lambda a=artist: self._open_booking(a)).pack(
            padx=20, pady=(8, 20), fill="x")

        return card

    def _open_booking(self, artist):
        def on_booked():
            messagebox.showinfo("Booking Confirmed",
                                "Your booking request has been sent!\n"
                                "The artist will confirm shortly.\n\n"
                                "Check 'My Bookings' to track your appointment.")
        BookingDialog(self, self.user, artist, on_booked)


class ClientBookingsPage(ctk.CTkScrollableFrame):
    """Client view: see their own bookings with cancel option."""

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.user = user
        self._build()

    def _build(self):
        section_title(self, "📅  My Bookings")

        from apps.bookings.models import Booking
        bookings = Booking.objects.filter(client=self.user).select_related(
            'service', 'service__artist__user'
        ).order_by('-created_at')

        if not bookings:
            ctk.CTkLabel(self,
                         text="You haven't made any bookings yet.\nBrowse artists to book your first appointment!",
                         font=ctk.CTkFont(size=14), text_color=TEXT2,
                         justify="center").pack(pady=60)
            return

        STATUS_COLOUR = {
            'pending':   WARNING,
            'confirmed': SUCCESS,
            'completed': "#1565C0",
            'cancelled': DANGER,
        }

        for b in bookings:
            try:
                artist_name = b.service.artist.user.get_full_name()
                svc_name    = b.service.name
                price       = f"${b.service.price}"
            except Exception:
                artist_name = svc_name = price = "—"

            date_str = b.booking_date.strftime("%d %b %Y") if b.booking_date else "—"
            status   = b.status

            card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=14,
                                border_width=1, border_color="#F0DCE8")
            card.pack(fill="x", pady=6)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=14)
            row.grid_columnconfigure(0, weight=1)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(info, text=svc_name,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=TEXT).pack(anchor="w")
            ctk.CTkLabel(info, text=f"💄 {artist_name}  •  📅 {date_str}  •  💰 {price}",
                         font=ctk.CTkFont(size=12), text_color=TEXT2).pack(anchor="w", pady=(2, 0))

            right = ctk.CTkFrame(row, fg_color="transparent")
            right.grid(row=0, column=1, sticky="e")

            clr = STATUS_COLOUR.get(status, TEXT2)
            ctk.CTkLabel(right, text=status.capitalize(),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=clr).pack(anchor="e")

            if status == 'pending':
                ctk.CTkButton(right, text="Cancel", height=30, width=90,
                              fg_color=DANGER, hover_color="#8B1A1A",
                              font=ctk.CTkFont(size=11), corner_radius=15,
                              command=lambda bid=b.id: self._cancel(bid)).pack(
                    anchor="e", pady=(6, 0))

    def _cancel(self, booking_id):
        if not messagebox.askyesno("Cancel Booking",
                                   "Are you sure you want to cancel this booking?"):
            return
        from apps.bookings.models import Booking
        try:
            b = Booking.objects.get(id=booking_id)
            b.status = 'cancelled'
            b.save()
            messagebox.showinfo("Cancelled", "Your booking has been cancelled.")
            # Refresh
            for widget in self.winfo_children():
                widget.destroy()
            self._build()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


class ClientProfilePage(ctk.CTkScrollableFrame):
    """Client view: edit their own profile."""

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.user = user
        self._build()

    def _build(self):
        section_title(self, "👤  My Profile")

        card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=16,
                            border_width=1, border_color="#F0DCE8")
        card.pack(padx=0, pady=8, fill="x")

        self._first = tk.StringVar(value=self.user.first_name or "")
        self._last  = tk.StringVar(value=self.user.last_name or "")
        self._phone = tk.StringVar(value=getattr(self.user, 'phone_number', '') or "")

        _form_field(card, "First Name", self._first)
        _form_field(card, "Last Name",  self._last)
        _form_field(card, "Phone Number", self._phone)

        ctk.CTkLabel(card, text=f"Email: {self.user.email}",
                     font=ctk.CTkFont(size=13), text_color=TEXT2).pack(
            anchor="w", padx=24, pady=(16, 4))

        self._msg = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=12))
        self._msg.pack(pady=(8, 0))

        ctk.CTkButton(card, text="Save Changes", height=48,
                      fg_color=PRIMARY, hover_color=PRIMARY_D,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      corner_radius=24, command=self._save).pack(
            padx=24, pady=(12, 24), fill="x")

    def _save(self):
        self.user.first_name = self._first.get().strip()
        self.user.last_name  = self._last.get().strip()
        if hasattr(self.user, 'phone_number'):
            self.user.phone_number = self._phone.get().strip()
        try:
            self.user.save()
            self._msg.configure(text="✅  Profile saved!", text_color=SUCCESS)
        except Exception as exc:
            self._msg.configure(text=f"Error: {exc}", text_color=DANGER)


# ══════════════════════════════════════════════════════════════════════════════
#  ARTIST PAGES
# ══════════════════════════════════════════════════════════════════════════════

class ArtistDashboardPage(ctk.CTkScrollableFrame):
    """Artist view: stats + recent bookings for their services."""

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.user = user
        self._build()

    def _build(self):
        section_title(self, f"Welcome back, {self.user.first_name or 'there'} 👋")

        from apps.bookings.models import Booking
        from apps.profiles.models import MakeupArtistProfile

        try:
            profile = MakeupArtistProfile.objects.get(user=self.user)
        except MakeupArtistProfile.DoesNotExist:
            ctk.CTkLabel(self, text="Artist profile not found. Please contact admin.",
                         font=ctk.CTkFont(size=14), text_color=DANGER).pack(pady=40)
            return

        qs = Booking.objects.filter(service__artist=profile)
        total     = qs.count()
        pending   = qs.filter(status='pending').count()
        confirmed = qs.filter(status='confirmed').count()
        completed = qs.filter(status='completed').count()

        try:
            from django.db.models import Sum
            earned = qs.filter(status='completed').aggregate(
                t=Sum('service__price'))['t'] or 0
            earned_str = f"${earned:,.2f}"
        except Exception:
            earned_str = "—"

        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 24))
        stats_frame.grid_columnconfigure((0,1,2,3), weight=1)

        cards = [
            ("Total Bookings", str(total),     PRIMARY),
            ("Pending",        str(pending),   WARNING),
            ("Confirmed",      str(confirmed), SUCCESS),
            ("Earnings",       earned_str,     "#1565C0"),
        ]
        for col, (title, val, color) in enumerate(cards):
            c = stat_card(stats_frame, title, val, color)
            c.grid(row=0, column=col, padx=8, sticky="ew")

        section_title(self, "Recent Bookings")

        recent = qs.select_related('client', 'service').order_by('-created_at')[:15]
        rows = []
        for b in recent:
            client = b.client.get_full_name() if hasattr(b, 'client') else "—"
            rows.append((
                client,
                b.service.name if b.service else "—",
                b.status.capitalize(),
                b.booking_date.strftime("%d %b %Y") if b.booking_date else "—",
                f"${b.service.price}" if b.service else "—",
            ))

        if rows:
            styled_table(self,
                columns=("Client","Service","Status","Date","Price"),
                rows=rows,
                col_widths={"Client":180,"Service":200,"Status":110,"Date":120,"Price":90},
            )
        else:
            ctk.CTkLabel(self, text="No bookings received yet.",
                         font=ctk.CTkFont(size=14), text_color=TEXT2).pack(pady=40)


class ArtistMyBookingsPage(ctk.CTkScrollableFrame):
    """Artist view: manage incoming bookings (confirm / complete / cancel)."""

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.user = user
        self._build()

    def _build(self):
        section_title(self, "📅  My Bookings")

        from apps.bookings.models import Booking
        from apps.profiles.models import MakeupArtistProfile

        try:
            profile = MakeupArtistProfile.objects.get(user=self.user)
        except MakeupArtistProfile.DoesNotExist:
            ctk.CTkLabel(self, text="Artist profile not found.",
                         font=ctk.CTkFont(size=14), text_color=DANGER).pack(pady=40)
            return

        bookings = Booking.objects.filter(
            service__artist=profile
        ).select_related('client', 'service').order_by('-created_at')

        if not bookings:
            ctk.CTkLabel(self, text="No bookings yet.",
                         font=ctk.CTkFont(size=14), text_color=TEXT2).pack(pady=60)
            return

        STATUS_COLOUR = {
            'pending':   WARNING,
            'confirmed': SUCCESS,
            'completed': "#1565C0",
            'cancelled': DANGER,
        }

        for b in bookings:
            client_name = b.client.get_full_name() if hasattr(b, 'client') else "—"
            svc_name    = b.service.name if b.service else "—"
            price       = f"${b.service.price}" if b.service else "—"
            date_str    = b.booking_date.strftime("%d %b %Y") if b.booking_date else "—"
            status      = b.status

            card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=14,
                                border_width=1, border_color="#F0DCE8")
            card.pack(fill="x", pady=6)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=14)
            row.grid_columnconfigure(0, weight=1)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(info, text=f"👤 {client_name}",
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=TEXT).pack(anchor="w")
            ctk.CTkLabel(info, text=f"✨ {svc_name}  •  📅 {date_str}  •  💰 {price}",
                         font=ctk.CTkFont(size=12), text_color=TEXT2).pack(anchor="w", pady=(2, 0))

            if b.notes:
                notes_preview = b.notes[:80] + ("…" if len(b.notes) > 80 else "")
                ctk.CTkLabel(info, text=f"📝 {notes_preview}",
                             font=ctk.CTkFont(size=11), text_color=TEXT2).pack(anchor="w")

            right = ctk.CTkFrame(row, fg_color="transparent")
            right.grid(row=0, column=1, sticky="e")

            clr = STATUS_COLOUR.get(status, TEXT2)
            ctk.CTkLabel(right, text=status.capitalize(),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=clr).pack(anchor="e")

            btn_frame = ctk.CTkFrame(right, fg_color="transparent")
            btn_frame.pack(anchor="e", pady=(6, 0))

            if status == 'pending':
                ctk.CTkButton(btn_frame, text="Confirm", height=30, width=80,
                              fg_color=SUCCESS, hover_color="#1B5E20",
                              font=ctk.CTkFont(size=11), corner_radius=15,
                              command=lambda bid=b.id: self._update(bid, 'confirmed')).pack(
                    side="left", padx=2)
                ctk.CTkButton(btn_frame, text="Decline", height=30, width=80,
                              fg_color=DANGER, hover_color="#8B1A1A",
                              font=ctk.CTkFont(size=11), corner_radius=15,
                              command=lambda bid=b.id: self._update(bid, 'cancelled')).pack(
                    side="left", padx=2)
            elif status == 'confirmed':
                ctk.CTkButton(btn_frame, text="Complete", height=30, width=90,
                              fg_color="#1565C0", hover_color="#0D47A1",
                              font=ctk.CTkFont(size=11), corner_radius=15,
                              command=lambda bid=b.id: self._update(bid, 'completed')).pack(
                    side="left", padx=2)

    def _update(self, booking_id, new_status):
        from apps.bookings.models import Booking
        try:
            b = Booking.objects.get(id=booking_id)
            b.status = new_status
            b.save()
            for widget in self.winfo_children():
                widget.destroy()
            self._build()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


class ArtistProfileEditPage(ctk.CTkScrollableFrame):
    """Artist view: edit their public profile."""

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.user = user
        self._build()

    def _build(self):
        section_title(self, "👤  My Profile")

        from apps.profiles.models import MakeupArtistProfile

        try:
            self.profile = MakeupArtistProfile.objects.get(user=self.user)
        except MakeupArtistProfile.DoesNotExist:
            self.profile = None

        card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=16,
                            border_width=1, border_color="#F0DCE8")
        card.pack(padx=0, pady=8, fill="x")

        self._first = tk.StringVar(value=self.user.first_name or "")
        self._last  = tk.StringVar(value=self.user.last_name or "")
        _form_field(card, "First Name", self._first)
        _form_field(card, "Last Name",  self._last)

        ctk.CTkLabel(card, text="Bio", font=ctk.CTkFont(size=13),
                     text_color=TEXT2).pack(anchor="w", padx=24, pady=(16, 4))
        self._bio = ctk.CTkTextbox(card, height=90, font=ctk.CTkFont(size=13),
                                   border_color=PRIMARY, border_width=1)
        if self.profile and self.profile.bio:
            self._bio.insert("1.0", self.profile.bio)
        self._bio.pack(padx=24, fill="x")

        self._location = tk.StringVar(
            value=(self.profile.location if self.profile else "") or "")
        self._rate = tk.StringVar(
            value=str(self.profile.hourly_rate if self.profile else "0.00"))

        _form_field(card, "Location", self._location)
        _form_field(card, "Hourly Rate ($)", self._rate)

        ctk.CTkLabel(card, text="Specialties (comma-separated)", font=ctk.CTkFont(size=13),
                     text_color=TEXT2).pack(anchor="w", padx=24, pady=(16, 4))
        specs = self.profile.specialties if self.profile else []
        self._specs = tk.StringVar(value=", ".join(specs) if specs else "")
        ctk.CTkEntry(card, textvariable=self._specs, height=44,
                     border_color=PRIMARY, font=ctk.CTkFont(size=14)).pack(padx=24, fill="x")

        # Available toggle
        avail_frame = ctk.CTkFrame(card, fg_color="transparent")
        avail_frame.pack(anchor="w", padx=24, pady=(16, 0))
        self._avail = tk.BooleanVar(value=(self.profile.is_available if self.profile else True))
        ctk.CTkCheckBox(avail_frame, text="Available for bookings",
                        variable=self._avail, font=ctk.CTkFont(size=13),
                        fg_color=PRIMARY, hover_color=PRIMARY_D,
                        text_color=TEXT).pack(side="left")

        self._msg = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=12))
        self._msg.pack(pady=(12, 0))

        ctk.CTkButton(card, text="Save Profile", height=48,
                      fg_color=PRIMARY, hover_color=PRIMARY_D,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      corner_radius=24, command=self._save).pack(
            padx=24, pady=(12, 24), fill="x")

    def _save(self):
        from apps.profiles.models import MakeupArtistProfile

        self.user.first_name = self._first.get().strip()
        self.user.last_name  = self._last.get().strip()
        try:
            self.user.save()
        except Exception as exc:
            self._msg.configure(text=f"Error saving user: {exc}", text_color=DANGER)
            return

        bio      = self._bio.get("1.0", "end").strip()
        location = self._location.get().strip()
        specs_raw = [s.strip() for s in self._specs.get().split(',') if s.strip()]
        try:
            rate = Decimal(self._rate.get().strip())
        except Exception:
            self._msg.configure(text="Invalid hourly rate.", text_color=DANGER)
            return

        try:
            profile, _ = MakeupArtistProfile.objects.get_or_create(user=self.user)
            profile.bio          = bio
            profile.location     = location
            profile.hourly_rate  = rate
            profile.is_available = self._avail.get()
            profile.specialties  = specs_raw
            profile.save()
            self._msg.configure(text="✅  Profile saved!", text_color=SUCCESS)
        except Exception as exc:
            self._msg.configure(text=f"Error: {exc}", text_color=DANGER)


class AddServiceDialog(ctk.CTkToplevel):
    """Modal to add a new service for an artist."""

    def __init__(self, parent, artist_profile, on_saved):
        super().__init__(parent)
        self.title("Add Service")
        self.geometry("460x520")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.grab_set()
        self.profile   = artist_profile
        self.on_saved  = on_saved
        self._center(parent)
        self._build()

    def _center(self, parent):
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        self.geometry(f"460x520+{px - 230}+{py - 260}")

    def _build(self):
        ctk.CTkLabel(self, text="✨  Add New Service",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=PRIMARY).pack(pady=(24, 16))

        card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=16,
                            border_width=1, border_color="#F0DCE8")
        card.pack(padx=24, fill="x")

        self._name  = tk.StringVar()
        self._price = tk.StringVar()
        self._dur   = tk.StringVar(value="60")
        _form_field(card, "Service Name", self._name, pady_top=20)
        _form_field(card, "Price ($)",    self._price)
        _form_field(card, "Duration (minutes)", self._dur)

        CATEGORIES = ["bridal", "glam", "natural", "editorial", "special_fx", "other"]
        ctk.CTkLabel(card, text="Category", font=ctk.CTkFont(size=13),
                     text_color=TEXT2).pack(anchor="w", padx=24, pady=(16, 4))
        self._cat = tk.StringVar(value=CATEGORIES[0])
        ctk.CTkOptionMenu(card, values=CATEGORIES, variable=self._cat,
                          fg_color=SURFACE, button_color=PRIMARY,
                          button_hover_color=PRIMARY_D, text_color=TEXT,
                          font=ctk.CTkFont(size=13)).pack(padx=24, fill="x")

        ctk.CTkLabel(card, text="Description", font=ctk.CTkFont(size=13),
                     text_color=TEXT2).pack(anchor="w", padx=24, pady=(16, 4))
        self._desc = ctk.CTkTextbox(card, height=70, font=ctk.CTkFont(size=13),
                                    border_color=PRIMARY, border_width=1)
        self._desc.pack(padx=24, fill="x")

        self._err = ctk.CTkLabel(card, text="", text_color=DANGER,
                                 font=ctk.CTkFont(size=12))
        self._err.pack(pady=(8, 0))

        ctk.CTkButton(card, text="Add Service", height=48,
                      fg_color=PRIMARY, hover_color=PRIMARY_D,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      corner_radius=24, command=self._save).pack(
            padx=24, pady=(12, 24), fill="x")

    def _save(self):
        from apps.services.models import Service

        name = self._name.get().strip()
        if not name:
            self._err.configure(text="Service name is required.")
            return

        try:
            price = Decimal(self._price.get().strip())
        except Exception:
            self._err.configure(text="Invalid price.")
            return

        try:
            duration = int(self._dur.get().strip())
        except Exception:
            self._err.configure(text="Invalid duration.")
            return

        desc = self._desc.get("1.0", "end").strip()

        try:
            Service.objects.create(
                artist=self.profile,
                name=name,
                description=desc,
                price=price,
                duration=duration,
                category=self._cat.get(),
                is_active=True,
            )
        except Exception as exc:
            self._err.configure(text=f"Error: {exc}")
            return

        self.destroy()
        self.on_saved()


class ArtistServicesPage(ctk.CTkScrollableFrame):
    """Artist view: manage their services."""

    def __init__(self, parent, user):
        super().__init__(parent, fg_color=BG, corner_radius=0)
        self.user = user
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(hdr, text="✨  My Services",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkButton(hdr, text="+ Add Service", height=36, width=130,
                      fg_color=PRIMARY, hover_color=PRIMARY_D,
                      font=ctk.CTkFont(size=13), corner_radius=18,
                      command=self._add_service).pack(side="right")

        from apps.profiles.models import MakeupArtistProfile
        from apps.services.models import Service

        try:
            self.profile = MakeupArtistProfile.objects.get(user=self.user)
        except MakeupArtistProfile.DoesNotExist:
            ctk.CTkLabel(self, text="Artist profile not found.",
                         font=ctk.CTkFont(size=14), text_color=DANGER).pack(pady=40)
            return

        services = Service.objects.filter(artist=self.profile).order_by('name')

        if not services:
            ctk.CTkLabel(self, text="You have no services yet. Click '+ Add Service' to create one.",
                         font=ctk.CTkFont(size=14), text_color=TEXT2).pack(pady=60)
            return

        for svc in services:
            card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=14,
                                border_width=1, border_color="#F0DCE8")
            card.pack(fill="x", pady=6)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=14)
            row.grid_columnconfigure(0, weight=1)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(info, text=svc.name,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=TEXT).pack(anchor="w")
            ctk.CTkLabel(info,
                         text=f"💰 ${svc.price}  •  ⏱ {svc.duration} min  •  {svc.category.capitalize()}",
                         font=ctk.CTkFont(size=12), text_color=TEXT2).pack(anchor="w", pady=(2, 0))

            right = ctk.CTkFrame(row, fg_color="transparent")
            right.grid(row=0, column=1, sticky="e")

            status_text = "Active ✅" if svc.is_active else "Inactive ⛔"
            status_color = SUCCESS if svc.is_active else DANGER
            ctk.CTkLabel(right, text=status_text,
                         font=ctk.CTkFont(size=12), text_color=status_color).pack(anchor="e")

            toggle_label = "Deactivate" if svc.is_active else "Activate"
            ctk.CTkButton(right, text=toggle_label, height=30, width=90,
                          fg_color=DANGER if svc.is_active else SUCCESS,
                          hover_color="#8B1A1A" if svc.is_active else "#1B5E20",
                          font=ctk.CTkFont(size=11), corner_radius=15,
                          command=lambda sid=svc.id, act=svc.is_active: self._toggle(sid, act)).pack(
                anchor="e", pady=(6, 0))

    def _toggle(self, svc_id, currently_active):
        from apps.services.models import Service
        try:
            s = Service.objects.get(id=svc_id)
            s.is_active = not currently_active
            s.save()
            for widget in self.winfo_children():
                widget.destroy()
            self._build()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _add_service(self):
        from apps.profiles.models import MakeupArtistProfile
        try:
            profile = MakeupArtistProfile.objects.get(user=self.user)
        except MakeupArtistProfile.DoesNotExist:
            messagebox.showerror("Error", "Artist profile not found.")
            return

        def on_saved():
            for widget in self.winfo_children():
                widget.destroy()
            self._build()

        AddServiceDialog(self, profile, on_saved)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════

class MainWindow(ctk.CTk):
    ADMIN_PAGES = {
        "dashboard": DashboardPage,
        "bookings":  BookingsPage,
        "artists":   ArtistsPage,
        "services":  ServicesPage,
        "clients":   ClientsPage,
    }
    CLIENT_PAGES = {
        "browse":      BrowseArtistsPage,
        "my_bookings": ClientBookingsPage,
        "profile":     ClientProfilePage,
    }
    ARTIST_PAGES = {
        "dashboard":   ArtistDashboardPage,
        "my_bookings": ArtistMyBookingsPage,
        "profile":     ArtistProfileEditPage,
        "services":    ArtistServicesPage,
    }

    def __init__(self, user, on_logout):
        super().__init__()
        self.user       = user
        self.on_logout  = on_logout
        self.title("GlamConnect")
        self.geometry("1280x820")
        self.minsize(1000, 650)
        self.configure(fg_color=BG)
        self._center()
        self._current_page = None
        self._page_classes = self._pages_for_role(user.role)
        self._default_page = self._default_for_role(user.role)
        self._build()
        self.show_page(self._default_page)

    def _pages_for_role(self, role):
        if role == 'client':
            return self.CLIENT_PAGES
        if role == 'artist':
            return self.ARTIST_PAGES
        return self.ADMIN_PAGES

    def _default_for_role(self, role):
        if role == 'client':
            return 'browse'
        return 'dashboard'

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = (sw - 1280) // 2
        y = (sh - 820)  // 2
        self.geometry(f"1280x820+{x}+{y}")

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, self.show_page, self._logout, self.user)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self._content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew", padx=28, pady=28)
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

    def show_page(self, key):
        if self._current_page:
            self._current_page.destroy()
        cls = self._page_classes.get(key, list(self._page_classes.values())[0])
        self._current_page = cls(self._content, self.user)
        self._current_page.grid(row=0, column=0, sticky="nsew")
        self.sidebar.set_active(key)

    def _logout(self):
        self.destroy()
        self.on_logout()


# ══════════════════════════════════════════════════════════════════════════════
#  REGISTER WINDOW
# ══════════════════════════════════════════════════════════════════════════════

class RegisterWindow(ctk.CTkToplevel):
    """Sign-up screen for new clients and artists."""

    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.on_success = on_success
        self.title("GlamConnect — Create Account")
        self.geometry("500x680")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.grab_set()
        self._center(parent)
        self._build()

    def _center(self, parent):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"500x680+{(sw-500)//2}+{(sh-680)//2}")

    def _build(self):
        ctk.CTkLabel(self, text="💄", font=ctk.CTkFont(size=52)).pack(pady=(28, 4))
        ctk.CTkLabel(self, text="Create Account",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=PRIMARY).pack()
        ctk.CTkLabel(self, text="Join GlamConnect today",
                     font=ctk.CTkFont(size=12), text_color=TEXT2).pack(pady=(2, 20))

        card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=18,
                            border_width=1, border_color="#F0DCE8")
        card.pack(padx=32, fill="x")

        self._first = tk.StringVar()
        self._last  = tk.StringVar()
        self._email = tk.StringVar()
        self._pass  = tk.StringVar()
        self._pass2 = tk.StringVar()

        _form_field(card, "First Name",       self._first, pady_top=20)
        _form_field(card, "Last Name",        self._last)
        _form_field(card, "Email address",    self._email)
        _form_field(card, "Password",         self._pass,  show="•")
        _form_field(card, "Confirm Password", self._pass2, show="•")

        ctk.CTkLabel(card, text="I am a…", font=ctk.CTkFont(size=13),
                     text_color=TEXT2).pack(anchor="w", padx=24, pady=(16, 6))

        role_frame = ctk.CTkFrame(card, fg_color="transparent")
        role_frame.pack(anchor="w", padx=24, pady=(0, 4))
        self._role = tk.StringVar(value="client")

        ctk.CTkRadioButton(role_frame, text="Client (I want to book artists)",
                           variable=self._role, value="client",
                           font=ctk.CTkFont(size=13), text_color=TEXT,
                           fg_color=PRIMARY).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(role_frame, text="Makeup Artist",
                           variable=self._role, value="artist",
                           font=ctk.CTkFont(size=13), text_color=TEXT,
                           fg_color=PRIMARY).pack(side="left")

        self._err = ctk.CTkLabel(card, text="", text_color=DANGER,
                                 font=ctk.CTkFont(size=12), wraplength=400)
        self._err.pack(pady=(10, 0))

        ctk.CTkButton(card, text="Create Account", height=50,
                      fg_color=PRIMARY, hover_color=PRIMARY_D,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      corner_radius=25, command=self._register).pack(
            padx=24, pady=(12, 24), fill="x")

        self.bind('<Return>', lambda _: self._register())

    def _register(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        first = self._first.get().strip()
        last  = self._last.get().strip()
        email = self._email.get().strip().lower()
        pwd   = self._pass.get()
        pwd2  = self._pass2.get()
        role  = self._role.get()

        if not first or not last:
            self._err.configure(text="Please enter your first and last name.")
            return
        if not email or '@' not in email:
            self._err.configure(text="Please enter a valid email address.")
            return
        if len(pwd) < 6:
            self._err.configure(text="Password must be at least 6 characters.")
            return
        if pwd != pwd2:
            self._err.configure(text="Passwords do not match.")
            return
        if User.objects.filter(email=email).exists():
            self._err.configure(text="An account with this email already exists.")
            return

        username = email.split('@')[0].replace('.', '_').replace('+', '_')
        base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}_{counter}"
            counter += 1

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=pwd,
                first_name=first,
                last_name=last,
                role=role,
                is_verified=True,
            )
        except Exception as exc:
            self._err.configure(text=f"Error creating account: {exc}")
            return

        if role == 'artist':
            from apps.profiles.models import MakeupArtistProfile
            try:
                MakeupArtistProfile.objects.get_or_create(
                    user=user,
                    defaults=dict(
                        bio='',
                        hourly_rate=Decimal('0.00'),
                        location='',
                        is_available=True,
                        specialties=[],
                    )
                )
            except Exception:
                pass

        self.destroy()
        self.on_success(user)


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════

class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.title("GlamConnect — Sign In")
        self.geometry("460x620")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"460x620+{(sw-460)//2}+{(sh-620)//2}")

    def _build(self):
        ctk.CTkLabel(self, text="💄", font=ctk.CTkFont(size=68)).pack(pady=(40, 4))
        ctk.CTkLabel(self, text="GlamConnect",
                     font=ctk.CTkFont(size=34, weight="bold"),
                     text_color=PRIMARY).pack()
        ctk.CTkLabel(self, text="Makeup Artist Booking Platform",
                     font=ctk.CTkFont(size=13), text_color=TEXT2).pack(pady=(2, 28))

        card = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=18,
                            border_width=1, border_color="#F0DCE8")
        card.pack(padx=36, fill="x")

        self.email_var = tk.StringVar(value="admin@glamconnect.com")
        self.pass_var  = tk.StringVar(value="Admin@1234!")
        _form_field(card, "Email address", self.email_var, pady_top=20)
        _form_field(card, "Password",      self.pass_var,  show="•")

        self.err = ctk.CTkLabel(card, text="", text_color=DANGER,
                                font=ctk.CTkFont(size=12))
        self.err.pack(pady=(10, 0))

        ctk.CTkButton(card, text="Sign In", height=50,
                      fg_color=PRIMARY, hover_color=PRIMARY_D,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      corner_radius=25, command=self._login).pack(
            padx=24, pady=(16, 16), fill="x")

        ctk.CTkLabel(card, text="─────────── or ───────────",
                     font=ctk.CTkFont(size=11), text_color="#CCBBCC").pack()

        ctk.CTkButton(card, text="Create Account",
                      height=44, fg_color="transparent",
                      border_color=PRIMARY, border_width=2,
                      hover_color="#FCE4EC",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      corner_radius=22, text_color=PRIMARY,
                      command=self._open_register).pack(
            padx=24, pady=(12, 20), fill="x")

        ctk.CTkLabel(self,
                     text="Demo: admin@glamconnect.com / Admin@1234!",
                     font=ctk.CTkFont(size=11), text_color=TEXT2).pack(pady=(12, 0))

        self.bind('<Return>', lambda _: self._login())

    def _open_register(self):
        RegisterWindow(self, self._on_register_success)

    def _on_register_success(self, user):
        # New account created — skip login, go straight in
        self.destroy()
        self.on_success(user)

    def _login(self):
        from django.contrib.auth import authenticate
        email = self.email_var.get().strip()
        pwd   = self.pass_var.get()
        if not email or not pwd:
            self.err.configure(text="Please enter email and password.")
            return
        try:
            user = authenticate(username=email, password=pwd)
            if user is None:
                self.err.configure(text="Incorrect email or password.")
                return
            self.destroy()
            self.on_success(user)
        except Exception as exc:
            self.err.configure(text=f"Error: {exc}")


# ══════════════════════════════════════════════════════════════════════════════
#  STARTUP  (loading splash shown while Django initialises)
# ══════════════════════════════════════════════════════════════════════════════

class SplashWindow(ctk.CTk):
    """Shown for a few seconds while Django sets up the database."""
    def __init__(self):
        super().__init__()
        self.title("GlamConnect")
        self.geometry("420x360")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"420x360+{(sw-420)//2}+{(sh-360)//2}")
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="💄", font=ctk.CTkFont(size=72)).pack(pady=(60, 8))
        ctk.CTkLabel(self, text="GlamConnect",
                     font=ctk.CTkFont(size=30, weight="bold"),
                     text_color=PRIMARY).pack()
        ctk.CTkLabel(self, text="Makeup Artist Booking Platform",
                     font=ctk.CTkFont(size=13), text_color=TEXT2).pack(pady=(4, 28))
        self.status = ctk.CTkLabel(self, text="Starting up…",
                                   font=ctk.CTkFont(size=13), text_color=TEXT2)
        self.status.pack()
        self.bar = ctk.CTkProgressBar(self, width=280,
                                      fg_color="#F8E8F2",
                                      progress_color=PRIMARY)
        self.bar.set(0)
        self.bar.pack(pady=12)
        self.bar.start()

    def set_status(self, msg):
        self.status.configure(text=msg)
        self.update()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def _run():
    app_dir, data_dir = _resolve_dirs()

    splash = SplashWindow()
    splash.set_status("Setting up database…")
    splash.update()

    try:
        _bootstrap_django(app_dir, data_dir)
    except Exception as exc:
        splash.destroy()
        messagebox.showerror(
            "GlamConnect — Startup Error",
            f"Could not initialise GlamConnect:\n\n{exc}\n\n"
            f"Error log: {os.path.join(data_dir, 'glamconnect_error.log')}"
        )
        return

    splash.set_status("Ready!")
    splash.after(600, splash.destroy)
    splash.mainloop()

    # Loop: login → main app → (logout → login again)
    while True:
        _user_holder = [None]

        def on_login(user):
            _user_holder[0] = user

        login = LoginWindow(on_login)
        login.mainloop()

        if _user_holder[0] is None:
            break  # Window closed without login

        _logout_flag = [False]

        def on_logout():
            _logout_flag[0] = True

        main = MainWindow(_user_holder[0], on_logout)
        main.mainloop()

        if not _logout_flag[0]:
            break  # Window closed normally


if __name__ == '__main__':
    try:
        _run()
    except Exception as exc:
        traceback.print_exc()
        try:
            messagebox.showerror("GlamConnect Error", str(exc))
        except Exception:
            pass
