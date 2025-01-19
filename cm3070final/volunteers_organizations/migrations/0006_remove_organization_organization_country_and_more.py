# Generated by Django 5.1.4 on 2025-01-12 11:24

import address.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0003_auto_20200830_1851'),
        ('volunteers_organizations', '0005_organization_organization_country_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='organization_country',
        ),
        migrations.AlterField(
            model_name='organization',
            name='organization_address',
            field=address.models.AddressField(on_delete=django.db.models.deletion.CASCADE, to='address.address'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='organization_name',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
