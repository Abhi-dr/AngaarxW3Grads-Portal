from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from accounts.models import Student, Instructor
from .hackathon_models import HackathonTeam, TeamMember, JoinRequest
from home.models import FlamesCourse

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.utils.text import slugify


# ========================================== NOTIFICATIONS =========================================
    
class Notification(models.Model):
    # course = models.ForeignKey(Course, on_delete=models.CASCADE, default=None)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_fixed = models.BooleanField(default=False)
    is_alert = models.BooleanField(default=False)
    
    type_choices = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
        ('success', 'Success'),
    ]
    
    type = models.CharField(max_length=20, choices=type_choices, default='info')
    expiration_date = models.DateTimeField(null=True, blank=True)

    timeStamp = models.DateTimeField(auto_now_add=True, blank=True)
    
    def is_active(self):
        if self.expiration_date:
            return timezone.now() < self.expiration_date
        return True
        
    def __str__(self):
        return self.title

# ======================================= Anonymous Message ========================================

class Anonymous_Message(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    message = models.TextField()
    reply = models.TextField(blank=True, null=True)
    is_replied = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.message
    
    # set the value of replied at automatically when reply is added
    
    def save(self, *args, **kwargs):
        if self.reply:
            self.is_replied = True
            self.replied_at = timezone.now()
        super(Anonymous_Message, self).save(*args, **kwargs)

# =========================================== FEEDBACK ============================================

class Feedback(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    
    timeStamp = models.DateTimeField(auto_now_add=True, blank=True)
    
    def __str__(self):
        return 'Message from ' + self.student.username
    
# ====================================== AI Questions Asked ============================================

class AIQuestion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=True, null=True)
    instructor = models.CharField(max_length=255, default="None")
    question = models.TextField(blank=True, null=True)
    answer = models.TextField(blank=True, null=True)
    asked_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.question
    
    class Meta:
        verbose_name = "AI Question"
        verbose_name_plural = "AI Questions"

# ===============================================================================================
# ====================================== ASSIGNMENTS ============================================
# ===============================================================================================

# =================================================== Course ==========================================


class Course(models.Model):
    
    name = models.CharField(max_length=100, db_index=True)  # Increased length and added index
    
    instructor = models.ForeignKey(
        'accounts.Instructor', 
        on_delete=models.CASCADE, 
        blank=True, null=True,
        related_name='courses'
    )
    
    description = models.TextField(max_length=500)  # Increased length for better descriptions
    
    thumbnail = models.ImageField(
        upload_to="course_images/", 
        blank=True, 
        null=True,
        help_text="Course thumbnail image"
    )
    
    slug = models.SlugField(unique=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name or "Unnamed Course"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'


class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('Coding', 'Coding'),
        ('Text', 'Text'),
        ('File', 'File'),
        ('Image', 'Image'),
        ('Link', 'Link')
    ]
    
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Published', 'Published'),
        ('Archived', 'Archived'),
    ]

    # Generic relation to support both Course and FlamesCourse
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    course = GenericForeignKey('content_type', 'object_id')
    
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    
    assignment_type = models.CharField(
        max_length=10, 
        choices=ASSIGNMENT_TYPES,
        db_index=True
    )
    
    due_date = models.DateTimeField(db_index=True)
    
    max_score = models.PositiveIntegerField(default=100)
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='Draft',
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields
    instructions = models.TextField(blank=True, help_text="Detailed instructions for students")
    allow_late_submission = models.BooleanField(default=False)
    
    late_penalty_per_day = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Percentage penalty per day (0-100)"
    )

    def __str__(self):
        return f"{self.title}"
    
    def clean(self):
        # Validate that content_type is either Course or FlamesCourse
        allowed_models = ['course', 'flamescourse']
        if self.content_type and self.content_type.model not in allowed_models:
            raise ValidationError(
                f"Assignments can only be associated with Course or FlamesCourse models"
            )
        
        # Validate late penalty
        if self.late_penalty_per_day < 0 or self.late_penalty_per_day > 100:
            raise ValidationError("Late penalty must be between 0 and 100 percent")

    @property
    def is_overdue(self):
        from django.utils import timezone        
        return self.due_date < timezone.now() if self.due_date else False
    
    @property
    def submission_count(self):
        return self.submissions.count()
    
    @property
    def pending_submissions_count(self):
        return self.submissions.filter(status='pending').count()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['due_date', 'status']),
        ]


class AssignmentSubmission(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='submissions'
    )
    
    student = models.ForeignKey(
        'accounts.Student', 
        on_delete=models.CASCADE, 
        related_name='assignment_submissions'
    )
    
    # Submission fields
    submission_text = models.TextField(blank=True)
    submission_file = models.FileField(
        upload_to='assignments/files/%Y/%m/', 
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'zip', 'txt', 'py', 'js', 'html', 'css']
        )],
        help_text="Allowed formats: PDF, DOC, DOCX, ZIP, TXT, PY, JS, HTML, CSS"
    )
    
    submission_image = models.ImageField(
        upload_to='assignments/images/%Y/%m/', 
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp']
        )],
        help_text="Allowed formats: JPG, JPEG, PNG, GIF, WEBP"
    )
    submission_code = models.TextField(blank=True)
    submission_link = models.URLField(blank=True)
    
    # Status and feedback
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='Pending',
        db_index=True
    )
    score = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Score out of assignment's max_score"
    )
    
    feedback = models.TextField(blank=True, help_text="Instructor feedback")
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(blank=True, null=True)
    
    # Legacy fields (keeping for backward compatibility)
    extra_info = models.TextField(blank=True)

    def clean(self):
        """Validate submission based on assignment type"""
        assignment_type = self.assignment.assignment_type
        
        submission_fields = {
            'Text': self.submission_text,
            'File': self.submission_file,
            'Image': self.submission_image,
            'Coding': self.submission_code,
            'Link': self.submission_link,
        }
        
        required_field = submission_fields.get(assignment_type)
        if not required_field:
            field_names = {
                'Text': 'Text',
                'File': 'File',
                'Image': 'Image', 
                'Coding': 'Code',
                'Link': 'Link'
            }
            raise ValidationError(
                f'{field_names[assignment_type]} submission is required for this assignment type.'
            )
        
        # Validate score doesn't exceed max_score
        if self.score is not None and self.score > self.assignment.max_score:
            raise ValidationError(
                f'Score cannot exceed maximum score of {self.assignment.max_score}'
            )

    def save(self, *args, **kwargs):
        self.clean()
        
        # Set graded_at when status changes to accepted/rejected
        if self.status in ['accepted', 'rejected'] and not self.graded_at:
            from django.utils import timezone
            self.graded_at = timezone.now()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.assignment.title} - {self.student.username}'
    
    @property
    def is_late(self):
        """Check if submission was made after due date"""
        return self.submitted_at > self.assignment.due_date
    
    @property
    def days_late(self):
        """Calculate how many days late the submission is"""
        if not self.is_late:
            return 0
        delta = self.submitted_at - self.assignment.due_date
        return delta.days
    
    @property 
    def penalty_applied(self):
        """Calculate penalty percentage for late submission"""
        if not self.is_late or not self.assignment.late_penalty_per_day:
            return 0
        return min(self.days_late * float(self.assignment.late_penalty_per_day), 100)
    
    @property
    def final_score(self):
        """Calculate final score after applying late penalty"""
        if self.score is None:
            return None
        penalty = self.penalty_applied
        return max(0, self.score - (self.score * penalty / 100))

    def get_color_based_on_status(self):
        """Get Bootstrap color class based on status"""
        color_map = {
            'pending': 'warning',
            'accepted': 'success', 
            'rejected': 'danger',
            'needs_revision': 'info'
        }
        return color_map.get(self.status, 'secondary')
    
    def get_submission_content(self):
        """Get the actual submission content based on assignment type"""
        type_field_map = {
            'text': self.submission_text,
            'file': self.submission_file,
            'image': self.submission_image,
            'coding': self.submission_code,
            'link': self.submission_link,
        }
        return type_field_map.get(self.assignment.assignment_type)

    class Meta:
        unique_together = [('assignment', 'student')]
        ordering = ['-submitted_at']
        verbose_name = 'Assignment Submission'
        verbose_name_plural = 'Assignment Submissions'
        indexes = [
            models.Index(fields=['status', 'submitted_at']),
            models.Index(fields=['assignment', 'status']),
        ]
