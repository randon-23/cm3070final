# Generated by Django 5.1.4 on 2025-01-16 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('volunteers_organizations', '0009_membership_valid_role_check'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='organization_profile_img',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
        migrations.AddField(
            model_name='organization',
            name='organization_website',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='volunteer',
            name='bio',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='volunteer',
            name='profile_img',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]
