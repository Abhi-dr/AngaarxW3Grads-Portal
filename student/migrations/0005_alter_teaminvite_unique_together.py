# Generated by Django 5.0.6 on 2025-03-11 07:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0004_hackathonteam_slug_alter_hackathonteam_description'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='teaminvite',
            unique_together=set(),
        ),
    ]
