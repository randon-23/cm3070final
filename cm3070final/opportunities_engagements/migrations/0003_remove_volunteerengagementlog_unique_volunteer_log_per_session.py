# Generated by Django 5.1.4 on 2025-03-07 04:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities_engagements', '0002_remove_volunteerengagementlog_unique_volunteer_log_per_session_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='volunteerengagementlog',
            name='unique_volunteer_log_per_session',
        ),
    ]
