# Generated by Django 4.2.22 on 2025-06-17 07:01

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='batches/thumbnails/')),
                ('required_fields', models.JSONField(blank=True, default=list)),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('scenario', models.TextField(blank=True, null=True)),
                ('description', models.TextField()),
                ('constraints', models.TextField(blank=True, null=True)),
                ('input_format', models.TextField(blank=True, null=True)),
                ('output_format', models.TextField(blank=True, null=True)),
                ('cpu_time_limit', models.FloatField(blank=True, default=1, null=True)),
                ('memory_limit', models.PositiveIntegerField(blank=True, default=256, null=True)),
                ('show_complete_driver_code', models.BooleanField(default=False)),
                ('difficulty_level', models.CharField(choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')], max_length=50)),
                ('youtube_link', models.URLField(blank=True, null=True)),
                ('position', models.PositiveIntegerField(default=0)),
                ('hint', models.TextField(blank=True, null=True)),
                ('slug', models.SlugField(blank=True, null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('parent_id', models.IntegerField(default=-1)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='accounts.student')),
            ],
            options={
                'verbose_name': 'Question',
                'verbose_name_plural': 'Questions',
                'ordering': ['position'],
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.TextField()),
                ('language', models.CharField(max_length=20)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Wrong Answer', 'Wrong Answer'), ('Runtime Error', 'Runtime Error'), ('Time Limit Exceeded', 'Time Limit Exceeded'), ('Compilation Error', 'Compilation Error')], default='Pending', max_length=50)),
                ('score', models.PositiveIntegerField(default=0)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='practice.question')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.student')),
            ],
        ),
        migrations.CreateModel(
            name='Streak',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_streak', models.PositiveIntegerField(default=1)),
                ('last_submission_date', models.DateField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.student')),
            ],
        ),
        migrations.CreateModel(
            name='Solution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language_id', models.IntegerField(default=0)),
                ('code', models.TextField()),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solutions', to='practice.question')),
            ],
        ),
        migrations.CreateModel(
            name='Sheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='sheets/thumbnails/')),
                ('custom_order', models.JSONField(default=dict)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('is_sequential', models.BooleanField(default=False)),
                ('is_enabled', models.BooleanField(default=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('batches', models.ManyToManyField(blank=True, related_name='sheets', to='practice.batch')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sheets', to='accounts.instructor')),
            ],
            options={
                'verbose_name': 'Sheet',
                'verbose_name_plural': 'Sheets',
            },
        ),
        migrations.CreateModel(
            name='RecommendedQuestions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('link', models.URLField()),
                ('platform', models.CharField(choices=[('LeetCode', 'LeetCode'), ('HackerRank', 'HackerRank'), ('GeeksForGeeks', 'GeeksForGeeks')], max_length=50)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recommended_questions', to='practice.question')),
            ],
        ),
        migrations.AddField(
            model_name='question',
            name='sheets',
            field=models.ManyToManyField(blank=True, related_name='questions', to='practice.sheet'),
        ),
        migrations.CreateModel(
            name='POD',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.datetime.now)),
                ('batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pods', to='practice.batch')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pods', to='practice.question')),
            ],
        ),
        migrations.CreateModel(
            name='EnrollmentRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Rejected', 'Rejected')], default='Pending', max_length=10)),
                ('request_date', models.DateTimeField(auto_now_add=True)),
                ('additional_data', models.JSONField(blank=True, default=dict)),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollment_requests', to='practice.batch')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollment_requests', to='accounts.student')),
            ],
        ),
        migrations.CreateModel(
            name='DriverCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language_id', models.IntegerField(default=0)),
                ('visible_driver_code', models.TextField()),
                ('complete_driver_code', models.TextField()),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='driver_codes', to='practice.question')),
            ],
        ),
        migrations.AddField(
            model_name='batch',
            name='students',
            field=models.ManyToManyField(related_name='batches', through='practice.EnrollmentRequest', to='accounts.student'),
        ),
        migrations.CreateModel(
            name='TestCase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_data', models.TextField()),
                ('expected_output', models.TextField()),
                ('explaination', models.TextField(blank=True, null=True)),
                ('is_sample', models.BooleanField(default=False)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_cases', to='practice.question')),
            ],
            options={
                'indexes': [models.Index(fields=['question'], name='practice_te_questio_ff3285_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='question',
            index=models.Index(fields=['position'], name='practice_qu_positio_cd3979_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='enrollmentrequest',
            unique_together={('student', 'batch')},
        ),
        migrations.AddIndex(
            model_name='drivercode',
            index=models.Index(fields=['question', 'language_id'], name='practice_dr_questio_dd3958_idx'),
        ),
    ]
