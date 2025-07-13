from django.db import models
from django.utils.timezone import now
from accounts.models import Student

class Achievement(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="achievements")
    title = models.CharField(max_length=255)
    description = models.TextField()
    achievement_type = models.CharField(max_length=255)
    date = models.DateField(default=now)
    
    def __str__(self):
        return f"{self.student.username} - {self.title}"

# =================================================================================================

# models.py

import uuid
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
from PIL import Image
import os


class EventCategory(models.Model):
    """Categories for different types of events"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=7, default='#007bff', help_text="Hex color code for UI")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Event Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Event(models.Model):
    """Main event model for certificate generation"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True, max_length=220)
    description = models.TextField()
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Event details
    start_date = models.DateField()
    end_date = models.DateField()
    duration_hours = models.PositiveIntegerField(help_text="Duration in hours")
    location = models.CharField(max_length=200, blank=True)
    is_online = models.BooleanField(default=False)
    
    # Certificate settings
    certificate_template = models.ForeignKey('CertificateTemplate', on_delete=models.SET_NULL, null=True, blank=True)
    requires_verification = models.BooleanField(default=True, help_text="Requires manual verification before certificate generation")
    auto_generate_certificates = models.BooleanField(default=False, help_text="Auto-generate certificates for all participants")
    
    # Organizer info
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    instructors = models.ManyToManyField(User, related_name='instructed_events', blank=True)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.start_date})"
    
    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'slug': self.slug})
    
    @property
    def total_participants(self):
        return self.participants.count()
    
    @property
    def certificates_generated(self):
        return self.certificates.filter(is_generated=True).count()
    
    @property
    def is_ongoing(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class CertificateTemplate(models.Model):
    """Templates for different certificate designs"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Template files
    template_image = models.ImageField(upload_to='certificate_templates/', help_text="Background template image")
    template_html = models.TextField(blank=True, help_text="HTML template for web view")
    template_css = models.TextField(blank=True, help_text="CSS styling for template")
    
    # Template settings
    width = models.PositiveIntegerField(default=1200, help_text="Template width in pixels")
    height = models.PositiveIntegerField(default=800, help_text="Template height in pixels")
    
    # Text positioning (as percentages)
    participant_name_x = models.FloatField(default=50.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    participant_name_y = models.FloatField(default=45.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    event_name_x = models.FloatField(default=50.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    event_name_y = models.FloatField(default=30.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    date_x = models.FloatField(default=50.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    date_y = models.FloatField(default=70.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Font settings
    font_family = models.CharField(max_length=100, default='Arial')
    font_size_name = models.PositiveIntegerField(default=48)
    font_size_event = models.PositiveIntegerField(default=36)
    font_size_details = models.PositiveIntegerField(default=24)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Validate template image dimensions
        if self.template_image:
            img = Image.open(self.template_image)
            if img.width != self.width or img.height != self.height:
                # Resize image to match template dimensions
                img = img.resize((self.width, self.height), Image.LANCZOS)
                img.save(self.template_image.path)
        super().save(*args, **kwargs)


class Participant(models.Model):
    """Event participants who will receive certificates"""
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    
    # Participant details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Additional fields
    organization = models.CharField(max_length=200, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    
    # Participation details
    registration_date = models.DateTimeField(auto_now_add=True)
    attendance_percentage = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    completion_status = models.CharField(max_length=20, choices=[
        ('registered', 'Registered'),
        ('attending', 'Attending'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ], default='registered')
    
    # Certificate eligibility
    is_eligible = models.BooleanField(default=False, help_text="Eligible for certificate")
    min_attendance_met = models.BooleanField(default=False)
    assessment_passed = models.BooleanField(default=False)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['event', 'email']
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['event', 'email']),
            models.Index(fields=['is_eligible']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.event.name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Auto-determine eligibility based on attendance and assessment
        if self.attendance_percentage >= 80 and self.assessment_passed:
            self.is_eligible = True
        super().save(*args, **kwargs)


class Certificate(models.Model):
    """Individual certificates for participants"""
    
    # Relations
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='certificates')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='certificates')
    template = models.ForeignKey(CertificateTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Certificate identifiers
    certificate_id = models.CharField(max_length=12, unique=True, db_index=True)
    verification_code = models.CharField(max_length=64, unique=True, db_index=True)
    
    # Certificate content
    issued_date = models.DateField(default=timezone.now)
    grade = models.CharField(max_length=20, blank=True, help_text="Grade or score if applicable")
    achievement_level = models.CharField(max_length=50, blank=True, help_text="e.g., Excellence, Merit, Pass")
    
    # File storage
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='certificate_thumbnails/', blank=True, null=True)
    
    # Status and security
    is_generated = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_revoked = models.BooleanField(default=False)
    revocation_reason = models.TextField(blank=True)
    
    # Analytics
    download_count = models.PositiveIntegerField(default=0)
    last_downloaded = models.DateTimeField(null=True, blank=True)
    verification_count = models.PositiveIntegerField(default=0)
    last_verified = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['event', 'participant']
        ordering = ['-issued_date']
        indexes = [
            models.Index(fields=['certificate_id']),
            models.Index(fields=['verification_code']),
            models.Index(fields=['event', 'is_generated']),
            models.Index(fields=['is_verified', 'is_revoked']),
        ]
    
    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.participant.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = self.generate_certificate_id()
        if not self.verification_code:
            self.verification_code = self.generate_verification_code()
        super().save(*args, **kwargs)
    
    def generate_certificate_id(self):
        """Generate unique certificate ID"""
        while True:
            cert_id = f"{self.event.slug[:3].upper()}{uuid.uuid4().hex[:6].upper()}"
            if not Certificate.objects.filter(certificate_id=cert_id).exists():
                return cert_id
    
    def generate_verification_code(self):
        """Generate secure verification code"""
        data = f"{self.participant.email}{self.event.slug}{timezone.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_verification_url(self):
        return reverse('verify_certificate', kwargs={'certificate_id': self.certificate_id})
    
    def increment_download_count(self):
        self.download_count += 1
        self.last_downloaded = timezone.now()
        self.save(update_fields=['download_count', 'last_downloaded'])
    
    def increment_verification_count(self):
        self.verification_count += 1
        self.last_verified = timezone.now()
        self.save(update_fields=['verification_count', 'last_verified'])
    
    @property
    def is_valid(self):
        """Check if certificate is valid (not revoked and verified)"""
        return not self.is_revoked and self.is_verified


class CertificateVerificationLog(models.Model):
    """Log all certificate verification attempts"""
    
    certificate = models.ForeignKey(Certificate, on_delete=models.CASCADE, related_name='verification_logs')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    verification_date = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-verification_date']
        indexes = [
            models.Index(fields=['certificate', 'verification_date']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"Verification for {self.certificate.certificate_id} - {self.verification_date}"


class BulkCertificateGeneration(models.Model):
    """Track bulk certificate generation jobs"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bulk_generations')
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Job details
    total_certificates = models.PositiveIntegerField(default=0)
    generated_certificates = models.PositiveIntegerField(default=0)
    failed_certificates = models.PositiveIntegerField(default=0)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    success_log = models.TextField(blank=True)
    error_log = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bulk generation for {self.event.name} - {self.status}"
    
    @property
    def completion_percentage(self):
        if self.total_certificates == 0:
            return 0
        return (self.generated_certificates / self.total_certificates) * 100