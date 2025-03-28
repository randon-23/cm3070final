# Generated by Django 5.1.4 on 2025-03-07 03:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities_engagements', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='volunteerengagementlog',
            name='unique_volunteer_log_per_session',
        ),
        migrations.AddConstraint(
            model_name='volunteerengagementlog',
            constraint=models.UniqueConstraint(condition=models.Q(('session__isnull', False)), fields=('volunteer_engagement', 'session'), name='unique_volunteer_log_per_session'),
        ),
    ]
