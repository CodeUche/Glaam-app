"""
Management command to create sample services for testing.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.profiles.models import MakeupArtistProfile
from apps.services.models import Service, ServiceCategory

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample services for testing and demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--artist-email',
            type=str,
            help='Email of the artist to create services for',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing services before creating new ones',
        )

    def handle(self, *args, **options):
        # Get artist
        if options['artist_email']:
            try:
                user = User.objects.get(email=options['artist_email'], role='artist')
                artist = user.artist_profile
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Artist with email {options["artist_email"]} not found'))
                return
            except MakeupArtistProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {options["artist_email"]} does not have an artist profile'))
                return
        else:
            # Get first available artist
            artist = MakeupArtistProfile.objects.first()
            if not artist:
                self.stdout.write(self.style.ERROR('No artist profiles found. Please create an artist first.'))
                return

        # Clear existing services if requested
        if options['clear']:
            deleted_count = Service.objects.filter(artist=artist).delete()[0]
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing services'))

        # Sample services data
        services_data = [
            {
                'name': 'Bridal Makeup Package',
                'description': 'Complete bridal makeup with pre-wedding trial, including airbrush foundation, contouring, eye makeup, and lip color. Perfect for your special day!',
                'category': ServiceCategory.BRIDAL,
                'price': Decimal('350.00'),
                'duration': 180,
            },
            {
                'name': 'Editorial Photoshoot Makeup',
                'description': 'High-fashion editorial makeup for photoshoots and magazine features. Includes creative eye looks and bold lip colors.',
                'category': ServiceCategory.EDITORIAL,
                'price': Decimal('200.00'),
                'duration': 120,
            },
            {
                'name': 'Natural Everyday Look',
                'description': 'Subtle, natural makeup that enhances your features for daily wear. Perfect for work or casual outings.',
                'category': ServiceCategory.NATURAL,
                'price': Decimal('80.00'),
                'duration': 60,
            },
            {
                'name': 'Glamour Night Out',
                'description': 'Full glam makeup for special events, parties, and nights out. Includes dramatic eyes, contoured cheeks, and bold lips.',
                'category': ServiceCategory.GLAM,
                'price': Decimal('150.00'),
                'duration': 90,
            },
            {
                'name': 'Airbrush Foundation Application',
                'description': 'Professional airbrush makeup for flawless, long-lasting coverage. Ideal for events and photography.',
                'category': ServiceCategory.AIRBRUSH,
                'price': Decimal('120.00'),
                'duration': 75,
            },
            {
                'name': 'Makeup Consultation',
                'description': 'One-on-one consultation to discuss your makeup needs, skin type, and personalized recommendations.',
                'category': ServiceCategory.CONSULTATION,
                'price': Decimal('50.00'),
                'duration': 45,
            },
            {
                'name': 'Special Effects Makeup',
                'description': 'Creative SFX makeup for Halloween, cosplay, theatrical performances, and film. Includes prosthetics and body painting.',
                'category': ServiceCategory.SFX,
                'price': Decimal('250.00'),
                'duration': 180,
            },
            {
                'name': 'Theatrical Stage Makeup',
                'description': 'Bold, dramatic makeup designed for stage performances and theatrical productions. Ensures visibility under stage lighting.',
                'category': ServiceCategory.THEATRICAL,
                'price': Decimal('175.00'),
                'duration': 90,
            },
        ]

        # Create services
        created_count = 0
        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                artist=artist,
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'category': service_data['category'],
                    'price': service_data['price'],
                    'duration': service_data['duration'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created service: {service.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Service already exists: {service.name}'))

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} services for {artist.user.full_name}'))
        self.stdout.write(self.style.SUCCESS(f'Total services: {Service.objects.filter(artist=artist).count()}'))
