# Generated by Django 5.0.6 on 2024-12-12 20:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('practice', '0007_remove_question_driver_code'),
    ]

    operations = [

        migrations.AddField(
            model_name='question',
            name='parent_id',
            field=models.IntegerField(default=-1),
        ),
        
    ]
