"""
Management command to manually update all artist ratings.
"""

from django.core.management.base import BaseCommand
from django.db.models import Avg
from apps.profiles.models import MakeupArtistProfile
from apps.reviews.models import Review


class Command(BaseCommand):
    """
    Update all artist ratings based on their reviews.

    Usage:
        python manage.py update_all_ratings
    """

    help = 'Update all artist ratings based on their visible reviews'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--artist-id',
            type=str,
            help='Update rating for specific artist (UUID)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed information',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        artist_id = options.get('artist_id')
        verbose = options.get('verbose')

        if artist_id:
            # Update specific artist
            try:
                artist = MakeupArtistProfile.objects.get(id=artist_id)
                self._update_artist_rating(artist, verbose)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated rating for {artist.user.full_name}')
                )
            except MakeupArtistProfile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Artist with ID {artist_id} not found')
                )
        else:
            # Update all artists
            artists = MakeupArtistProfile.objects.all()
            total = artists.count()
            updated = 0

            self.stdout.write(f'Updating ratings for {total} artists...')

            for artist in artists:
                if self._update_artist_rating(artist, verbose):
                    updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated} out of {total} artist ratings'
                )
            )

    def _update_artist_rating(self, artist, verbose=False):
        """
        Update rating for a single artist.

        Args:
            artist: MakeupArtistProfile instance
            verbose: Print detailed information

        Returns:
            bool: True if rating was changed
        """
        reviews = Review.objects.filter(artist=artist, is_visible=True)
        total_reviews = reviews.count()

        old_rating = artist.average_rating
        old_count = artist.total_reviews

        if total_reviews > 0:
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            artist.average_rating = round(avg_rating, 2)
            artist.total_reviews = total_reviews
        else:
            artist.average_rating = 0.0
            artist.total_reviews = 0

        # Check if anything changed
        changed = (
            artist.average_rating != old_rating or
            artist.total_reviews != old_count
        )

        if changed:
            artist.save(update_fields=['average_rating', 'total_reviews', 'updated_at'])

            if verbose:
                self.stdout.write(
                    f'  {artist.user.full_name}: '
                    f'{old_rating} → {artist.average_rating} '
                    f'({artist.total_reviews} reviews)'
                )

        return changed
