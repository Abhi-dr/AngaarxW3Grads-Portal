# Generated by Django 5.0.6 on 2024-12-17 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='coins',
            field=models.IntegerField(default=100),
        ),
    ]