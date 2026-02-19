# Clean squashed initial migration for accounts app.
# Represents the final state after Phase 1 migration:
#   - CustomUser(AbstractUser) replaces old MTI Student/Instructor/Administrator
#   - Student/Instructor/Administrator are now proxy models (no separate DB tables)
#   - PasswordResetToken and EmailVerificationToken FK to CustomUser
#
# IMPORTANT: Run with --fake-initial on existing databases since:
#   - accounts_customuser table is NEW (will be created)
#   - Old Student/Instructor/Administrator tables already exist in DB (leave them for now)
#
# Data copy from auth_user → accounts_customuser is handled by 0002_copy_user_data.py

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # ── CustomUser (main table — accounts_customuser) ─────────────────────
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password',    models.CharField(max_length=128, verbose_name='password')),
                ('last_login',  models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='superuser status')),
                ('username', models.CharField(
                    error_messages={'unique': 'A user with that username already exists.'},
                    max_length=150, unique=True,
                    validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                    verbose_name='username',
                )),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name',  models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email',      models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('is_staff',   models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active',  models.BooleanField(default=True, verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                # Custom fields
                ('role',                models.CharField(choices=[('student','Student'),('instructor','Instructor'),('admin','Administrator')], db_index=True, default='student', max_length=20)),
                ('mobile_number',       models.CharField(blank=True, max_length=10, null=True)),
                ('gender',              models.CharField(blank=True, max_length=19, null=True)),
                ('college',             models.CharField(blank=True, max_length=100, null=True)),
                ('dob',                 models.DateField(blank=True, null=True)),
                ('profile_pic',         models.ImageField(blank=True, default='/student_profile/default.jpg', null=True, upload_to='profiles/')),
                ('linkedin_id',         models.URLField(blank=True, null=True)),
                ('github_id',           models.URLField(blank=True, null=True)),
                ('coins',               models.IntegerField(default=100)),
                ('is_changed_password', models.BooleanField(default=False)),
                ('is_email_verified',   models.BooleanField(default=False)),
                # AbstractUser M2M
                ('groups', models.ManyToManyField(
                    blank=True,
                    help_text='The groups this user belongs to.',
                    related_name='customuser_set',
                    to='auth.group',
                    verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    help_text='Specific permissions for this user.',
                    related_name='customuser_set',
                    to='auth.permission',
                    verbose_name='user permissions',
                )),
            ],
            options={
                'verbose_name':        'User',
                'verbose_name_plural': 'Users',
                'db_table':            'accounts_customuser',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),

        # ── Proxy models (no DB tables — same accounts_customuser table) ──────
        migrations.CreateModel(
            name='Student',
            fields=[],
            options={
                'verbose_name':        'Student (Proxy)',
                'verbose_name_plural': 'Students (Proxy)',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('accounts.customuser',),
        ),
        migrations.CreateModel(
            name='Instructor',
            fields=[],
            options={
                'verbose_name':        'Instructor (Proxy)',
                'verbose_name_plural': 'Instructors (Proxy)',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('accounts.customuser',),
        ),
        migrations.CreateModel(
            name='Administrator',
            fields=[],
            options={
                'verbose_name':        'Administrator (Proxy)',
                'verbose_name_plural': 'Administrators (Proxy)',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('accounts.customuser',),
        ),

        # ── Indexes ───────────────────────────────────────────────────────────
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['role'],              name='accounts_cu_role_idx'),
        ),
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['email'],             name='accounts_cu_email_idx'),
        ),
        migrations.AddIndex(
            model_name='customuser',
            index=models.Index(fields=['is_active', 'role'], name='accounts_cu_active_role_idx'),
        ),

        # ── PasswordResetToken (FK → CustomUser) ──────────────────────────────
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_hash', models.CharField(max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('user',       models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='password_reset_tokens',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),

        # ── EmailVerificationToken (FK → CustomUser) ──────────────────────────
        migrations.CreateModel(
            name='EmailVerificationToken',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_hash', models.CharField(max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('user',       models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='email_verification_tokens',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
