# Generated by Django 5.0.6 on 2024-12-19 15:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_administrator'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='administrator',
            options={'verbose_name': 'Administrator', 'verbose_name_plural': 'Administrators'},
        ),
    ]