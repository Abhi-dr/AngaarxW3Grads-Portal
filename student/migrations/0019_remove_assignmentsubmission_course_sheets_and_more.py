# Generated by Django 5.1.5 on 2025-06-06 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0018_coursesheet_assignmentsubmission_course_sheets'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assignmentsubmission',
            name='course_sheets',
        ),
        migrations.AddField(
            model_name='assignment',
            name='course_sheets',
            field=models.ManyToManyField(blank=True, related_name='assignments', to='student.coursesheet'),
        ),
    ]
