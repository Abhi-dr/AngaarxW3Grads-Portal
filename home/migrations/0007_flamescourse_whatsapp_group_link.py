# Generated by Django 5.0.6 on 2025-05-10 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_flamesregistration_payable_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='flamescourse',
            name='whatsapp_group_link',
            field=models.URLField(blank=True, null=True),
        ),
    ]
