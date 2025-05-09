# Generated by Django 5.1.3 on 2024-11-23 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homifi_app', '0004_alter_user_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='location',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('renter', 'Renter'), ('landlord', 'Landlord')], default='renter', max_length=10),
        ),
    ]
