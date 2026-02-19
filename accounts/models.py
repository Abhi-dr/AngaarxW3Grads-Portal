from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import hashlib
import secrets


# =============================================================================
# CUSTOM USER MANAGER
# =============================================================================

class CustomUserManager(BaseUserManager):
    """
    Custom manager for CustomUser. Email is the unique identifier.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email)
        # Auto-generate username from email if not provided
        if not extra_fields.get('username'):
            base = email.split('@')[0]
            username = base
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base}{counter}"
                counter += 1
            extra_fields['username'] = username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


# =============================================================================
# ROLE-FILTERED MANAGERS (drop-in replacements for old model managers)
# =============================================================================

class StudentManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(role='student')


class InstructorManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(role='instructor')


class AdminManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(role='admin')


# =============================================================================
# CUSTOM USER — The single identity table
# =============================================================================

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student',    'Student'),
        ('instructor', 'Instructor'),
        ('admin',      'Administrator'),
    ]

    # Identity
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='student', db_index=True
    )

    # Override AbstractUser.email to enforce uniqueness (required for USERNAME_FIELD)
    email = models.EmailField(unique=True, verbose_name='email address')

    # Contact / Profile
    mobile_number        = models.CharField(max_length=10, blank=True, null=True)
    gender               = models.CharField(max_length=19, blank=True, null=True)
    college              = models.CharField(max_length=100, blank=True, null=True)
    dob                  = models.DateField(blank=True, null=True)
    profile_pic          = models.ImageField(
        upload_to="profiles/", blank=True, null=True,
        default="/student_profile/default.jpg"
    )
    linkedin_id          = models.URLField(blank=True, null=True)
    github_id            = models.URLField(blank=True, null=True)

    # Gamification
    coins                = models.IntegerField(default=100)

    # Auth state
    is_changed_password  = models.BooleanField(default=False)
    is_email_verified    = models.BooleanField(default=False)

    # Required for email-based login
    # email is already declared with unique=True above — satisfies auth.W004
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']   # username kept for allauth compatibility

    # Managers
    objects     = CustomUserManager()
    students    = StudentManager()
    instructors = InstructorManager()
    admins      = AdminManager()

    class Meta:
        verbose_name        = 'User'
        verbose_name_plural = 'Users'
        db_table            = 'accounts_customuser'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'role']),
        ]

    def __str__(self):
        return f"{self.email} ({self.role})"

    # ── Role helpers ──────────────────────────────────────────────────────────
    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_instructor(self):
        return self.role == 'instructor'

    @property
    def is_admin_user(self):
        return self.role == 'admin'

    # ── Profile completeness score (preserved from old Student model) ─────────
    def get_profile_score(self):
        score = 30
        if self.dob:         score += 20
        if self.linkedin_id: score += 30
        if self.github_id:   score += 20
        return score


# =============================================================================
# BACKWARD-COMPAT PROXY MODELS
# These let ALL existing views / querysets work without any change
# during Phase 1.  Remove them in Phase 2 after view layer is cleaned up.
# =============================================================================

class Student(CustomUser):
    """
    Proxy model — behaves exactly like old Student(User).
    All FK relations, QuerySets, and view code using Student still work.
    """
    objects = StudentManager()

    class Meta:
        proxy               = True
        verbose_name        = 'Student'
        verbose_name_plural = 'Students'

    def save(self, *args, **kwargs):
        self.role = 'student'
        super().save(*args, **kwargs)


class Instructor(CustomUser):
    """
    Proxy model — behaves exactly like old Instructor(User).
    """
    objects = InstructorManager()

    class Meta:
        proxy               = True
        verbose_name        = 'Instructor'
        verbose_name_plural = 'Instructors'

    def save(self, *args, **kwargs):
        self.role = 'instructor'
        super().save(*args, **kwargs)


class Administrator(CustomUser):
    """
    Proxy model — behaves exactly like old Administrator(User).
    """
    objects = AdminManager()

    class Meta:
        proxy               = True
        verbose_name        = 'Administrator'
        verbose_name_plural = 'Administrators'

    def save(self, *args, **kwargs):
        self.role = 'admin'
        super().save(*args, **kwargs)


# =============================================================================
# PASSWORD RESET TOKEN  (FK updated to CustomUser)
# =============================================================================

class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    @classmethod
    def create_token(cls, user):
        cls.objects.filter(user=user).delete()
        raw_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        cls.objects.create(user=user, token_hash=hashed_token)
        return raw_token

    def is_valid(self, token):
        hashed_input = hashlib.sha256(token.encode()).hexdigest()
        return hashed_input == self.token_hash and timezone.now() < self.expires_at

    def invalidate(self):
        self.delete()

    def __str__(self):
        return f"Password Reset Token for {self.user.email}"


# =============================================================================
# EMAIL VERIFICATION TOKEN  (FK updated to CustomUser)
# =============================================================================

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='email_verification_tokens'
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    @classmethod
    def create_token(cls, user):
        cls.objects.filter(user=user).delete()
        raw_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        cls.objects.create(user=user, token_hash=hashed_token)
        return raw_token

    def is_valid(self, token):
        hashed_input = hashlib.sha256(token.encode()).hexdigest()
        return hashed_input == self.token_hash and timezone.now() < self.expires_at

    def invalidate(self):
        self.delete()

    def __str__(self):
        return f"Email Verification Token for {self.user.email}"
