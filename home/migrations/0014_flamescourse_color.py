# Generated by Django 5.0.6 on 2025-03-25 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0013_flamescourse_discount_price_flamescourse_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='flamescourse',
            name='color',
            field=models.CharField(default=1, help_text='Color for the course card', max_length=200),
            preserve_default=False,
        ),
    ]
