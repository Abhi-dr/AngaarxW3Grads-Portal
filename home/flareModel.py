from django.db import models
from django.core.validators import RegexValidator
import json


class FlareRegistration(models.Model):
    """Model to store FLARE 1.0 program registrations"""
    
    # Occupation Status Choices
    OCCUPATION_CHOICES = [
        ('school_student', 'School Student'),
        ('undergrad_student', 'Undergraduation Student'),
        ('postgrad_student', 'Post Graduation Student'),
        ('working_professional', 'Working Professional'),
        ('not_working', 'Currently Not Working Anywhere'),
    ]
    
    # Course Choices (stored as JSON for multi-select)
    COURSE_CHOICES = [
        'Java + DSA',
        'Full Stack with Gen AI',
        'Data Analytics'
    ]
    
    # Career Goals Choices (stored as JSON for multi-select)
    CAREER_GOALS_CHOICES = [
        'Getting a Job in Tech',
        'Securing an Internship',
        'Making a Career Switch/Transition',
        'Upskilling/Acquiring New Expertise',
        'Entrepreneurship/Starting a Venture'
    ]
    
    # Phone number validator
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    # Model Fields
    email = models.EmailField(
        unique=True,
        verbose_name="Email Address",
        help_text="User's email address"
    )
    
    full_name = models.CharField(
        max_length=200,
        verbose_name="Full Name",
        help_text="User's full name"
    )
    
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        verbose_name="Phone Number",
        help_text="User's contact number"
    )
    
    occupation_status = models.CharField(
        max_length=50,
        choices=OCCUPATION_CHOICES,
        verbose_name="Current Occupation Status",
        help_text="User's current occupation/education status"
    )
    
    current_year = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Current Year of Study",
        help_text="Applicable for students only"
    )
    
    courses_interested = models.TextField(
        verbose_name="Courses Interested In",
        help_text="JSON array of selected courses"
    )
    
    career_goals = models.TextField(
        verbose_name="Career Goals",
        help_text="JSON array of selected career goals"
    )
    
    motivation = models.TextField(
        verbose_name="Motivation",
        help_text="What motivates the user to achieve their goals"
    )
    
    commitment = models.BooleanField(
        default=False,
        verbose_name="Ready to Commit",
        help_text="User's commitment to the program"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Registration Date",
        help_text="Timestamp when the registration was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Updated",
        help_text="Timestamp when the registration was last updated"
    )
    
    class Meta:
        verbose_name = "FLARE Registration"
        verbose_name_plural = "FLARE Registrations"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.email}"
    
    def get_courses_list(self):
        """Return courses as Python list"""
        try:
            return json.loads(self.courses_interested)
        except:
            return []
    
    def get_career_goals_list(self):
        """Return career goals as Python list"""
        try:
            return json.loads(self.career_goals)
        except:
            return []
    
    def set_courses_list(self, courses_list):
        """Set courses from Python list"""
        self.courses_interested = json.dumps(courses_list)
    
    def set_career_goals_list(self, goals_list):
        """Set career goals from Python list"""
        self.career_goals = json.dumps(goals_list)
