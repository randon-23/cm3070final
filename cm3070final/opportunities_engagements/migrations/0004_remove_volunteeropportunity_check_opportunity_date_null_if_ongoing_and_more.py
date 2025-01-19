# Generated by Django 5.1.4 on 2025-01-13 23:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities_engagements', '0003_volunteeropportunity_opportunity_date_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='volunteeropportunity',
            name='check_opportunity_date_null_if_ongoing',
        ),
        migrations.RemoveConstraint(
            model_name='volunteeropportunity',
            name='check_opportunity_date_not_null_if_not_ongoing',
        ),
    ]
