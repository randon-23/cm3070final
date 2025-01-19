# Generated by Django 5.1.4 on 2025-01-13 09:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('volunteers_organizations', '0007_alter_following_followed_organization_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='following',
            name='followed_organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='organization_followee', to='volunteers_organizations.organization'),
        ),
        migrations.AlterField(
            model_name='following',
            name='followed_volunteer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='volunteer_followee', to='volunteers_organizations.volunteer'),
        ),
    ]
