from django.db import migrations
from django.db.models import Index

class Migration(migrations.Migration):
    dependencies = [
        ('homifi_app', '0005_user_location_alter_user_role'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='property',
            index=Index(fields=['is_available', 'created_at'], name='property_available_created_idx_new'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=Index(fields=['owner'], name='property_owner_idx_new'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=Index(fields=['property_type'], name='property_type_idx_new'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=Index(fields=['listing_type'], name='property_listing_type_idx_new'),
        ),
        migrations.AddIndex(
            model_name='property',
            index=Index(fields=['city', 'state'], name='property_location_idx_new'),
        ),
        migrations.AddIndex(
            model_name='inquiry',
            index=Index(fields=['property', 'is_read'], name='inquiry_property_read_idx_new'),
        ),
        migrations.AddIndex(
            model_name='inquiry',
            index=Index(fields=['user'], name='inquiry_user_idx_new'),
        ),
        migrations.AddIndex(
            model_name='favorite',
            index=Index(fields=['user', 'property'], name='favorite_user_property_idx_new'),
        ),
        migrations.AddIndex(
            model_name='savedsearch',
            index=Index(fields=['user', 'created_at'], name='savedsearch_user_created_idx_new'),
        ),
    ] 