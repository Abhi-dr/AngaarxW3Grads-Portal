# Generated by Django 5.0.6 on 2024-12-08 04:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('practice', '0006_sheet_is_enabled'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='driver_code',
        ),
    ]
