# Generated by Django 5.0.6 on 2025-03-25 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0011_flamescourseinstructor_flamescourse_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flamescourse',
            name='instructor',
            field=models.CharField(max_length=200),
        ),
        migrations.RemoveField(
            model_name='flamescourse',
            name='color',
        ),
        migrations.RemoveField(
            model_name='flamescourse',
            name='updated_at',
        ),
        migrations.DeleteModel(
            name='FlamesCourseInstructor',
        ),
    ]
