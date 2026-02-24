# Migration to add review_reminder and review_response notification types
# and update the field to use the new NotificationType choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('booking_request', 'Booking Request'),
                    ('new_booking', 'New Booking'),
                    ('booking_accepted', 'Booking Accepted'),
                    ('booking_rejected', 'Booking Rejected'),
                    ('booking_completed', 'Booking Completed'),
                    ('booking_cancelled', 'Booking Cancelled'),
                    ('booking_reminder', 'Booking Reminder'),
                    ('review_received', 'Review Received'),
                    ('review_reminder', 'Review Reminder'),
                    ('review_response', 'Review Response'),
                    ('system', 'System'),
                ],
                default='system',
                max_length=50,
            ),
        ),
    ]
