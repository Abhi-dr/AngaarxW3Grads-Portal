from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.models import User
from accounts.models import Student, Instructor

from datetime import datetime, timedelta

    
# ======================= JOB ARTICLE MODEL ======================

class Article(models.Model):
    title = models.CharField(max_length=100)
    content = RichTextUploadingField()
    thumbnail = models.ImageField(upload_to="thumbnails/")
    likes = models.ManyToManyField(User, related_name='liked_articles', blank=True)
    
    slug = models.SlugField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        
    def __str__(self):
        return self.title
    
    def total_likes(self):
        return self.likes.count()
    
    def save(self, *args, **kwargs):
        if not self.slug:
            text = ""
        
            for word in self.title.split():
                if word.isalnum():
                    text += word + "-"
                else:
                    word = ''.join(e for e in word if e.isalnum())
                    text += word + "-"
            
            # Generate base slug
            base_slug = text.lower().strip("-")
            slug = base_slug

            # Check for uniqueness
            counter = 1
            while Article.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug
        super(Article, self).save(*args, **kwargs)

# ======================= COMMENT MODEL ======================

class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f'Comment by {self.user.username} on {self.article.title}'

# ========================== FLAMES ===========================

class FlamesCourse(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=255)
    description = models.TextField()
    
    instructor = models.ManyToManyField(Instructor, related_name='flames_courses', blank=True)
    
    
    what_you_will_learn = models.TextField(help_text="Enter points separated by new lines")
    
    roadmap = models.TextField(help_text="Course roadmap details")
    
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    icon_class = models.CharField(max_length=50, help_text="Font Awesome icon class")
    icon_color = models.CharField(max_length=200, help_text="Color for the course card")
    button_color = models.CharField(max_length=200, help_text="Color for the course button")
    
    whatsapp_group_link = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    def get_learning_points(self):
        """Return what_you_will_learn as a list of points"""
        return self.what_you_will_learn.strip().split('\n')
    
    def get_all_instructors(self):
        """Return a list of all instructors for this course"""
        names = []
        for instructor in self.instructor.all():
            names.append(instructor.first_name)
        return ' & '.join(names)

# ================= FLAMES COURSE TESTIMONIALS ======================

class FlamesCourseTestimonial(models.Model):
    course = models.ForeignKey(FlamesCourse, on_delete=models.CASCADE, related_name='testimonials')
    student_name = models.CharField(max_length=100)
    student_image = models.ImageField(upload_to="flames/testimonials/", blank=True, null=True)
    content = models.TextField()
    rating = models.IntegerField(default=5, choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    
    def __str__(self):
        return f"Testimonial by {self.student_name} for {self.course.title}"

class Alumni(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    college = models.CharField(max_length=200, blank=True, null=True)
    batch_year = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class ReferralCode(models.Model):
    REFERRAL_TYPE_CHOICES = [
        ('ALUMNI', 'Alumni Referral'),
        ('TEAM', 'Team Referral'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    referral_type = models.CharField(max_length=10, choices=REFERRAL_TYPE_CHOICES)
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='referral_codes', null=True, blank=True)
    discount_amount = models.IntegerField(default=499, help_text="Discount amount in percentage")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        if self.referral_type == 'ALUMNI':
            return f"Alumni Referral: {self.code} ({self.alumni.name if self.alumni else 'No alumni'})"
        return f"Team Referral: {self.code}"
    
    @classmethod
    def generate_unique_code(cls, prefix='FLAME', length=8):
        """Generate a unique referral code"""
        import random
        import string
        
        while True:
            # Generate random string of specified length
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            code = f"{prefix}{random_part}"
            
            # Check if code already exists
            if not cls.objects.filter(code=code).exists():
                return code

# ================= FLAMES REGISTRATIONS ======================

class FlamesRegistration(models.Model):
    
    user = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='flames_registrations')
    team = models.ForeignKey('FlamesTeam', on_delete=models.SET_NULL, null=True, blank=True, related_name='registrations')
    
    course = models.ForeignKey(FlamesCourse, on_delete=models.CASCADE, related_name='registrations')
    
    year = models.CharField(max_length=20)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    status = models.CharField(max_length=20, default="Pending", 
                             choices=[("Pending", "Pending"), 
                                     ("Approved", "Approved"), 
                                     ("Rejected", "Rejected"),
                                     ("Completed", "Completed")])
    
    admin_notes = models.TextField(blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
   
    registration_mode = models.CharField(max_length=10, default="SOLO", 
                                        choices=[("SOLO", "Solo Registration"), 
                                                ("TEAM", "Team Registration")])
    
    referral_code = models.ForeignKey(ReferralCode, on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='registrations')
    
    original_price = models.IntegerField(blank=True, null=True)
    discounted_price = models.IntegerField(blank=True, null=True)
    payable_amount = models.IntegerField(blank=True, null=True)
    

    
    # Create method to update existing records with default values (for migration)
    @classmethod
    def set_default_status(cls):
        for registration in cls.objects.filter(status__isnull=True):
            registration.status = "Pending"
            registration.save(update_fields=['status'])
            
    def save(self, *args, **kwargs):
        # Check if this is a new registration (no ID yet) or price fields haven't been set
        is_new = not self.pk or not self.original_price
        
        # Only calculate pricing when object is new or price-related fields have changed
        # Get the previous instance if it exists to check for changes
        if is_new:
            # Set the original price from the course
            if not self.original_price:
                # For both solo and team registrations, use the same course price
                self.original_price = self.course.discount_price
                self.discounted_price = self.course.discount_price  # Initialize discounted price
                
            # Apply discount if referral code is provided
            if self.referral_code and self.referral_code.is_active:
                discount = self.referral_code.discount_amount
                # Apply discount to the discounted_price instead of original_price
                self.discounted_price -= discount
            
            # Calculate payable amount based on registration mode
            if self.registration_mode == 'TEAM':
                # Team payable amount is total amount (discount_price * 5) minus the team discount (499 * 5)
                self.payable_amount = (self.discounted_price * 5) - (499 * 5)
            else:
                self.payable_amount = self.discounted_price
        
        super().save(*args, **kwargs)
        
    # a function to get the total amount we have generated so par (based on payable amount)
    @classmethod
    def get_total_amount(cls):
        total = 0
        for registration in cls.objects.all():
            if registration.payable_amount and registration.status == "Completed":
                total += registration.payable_amount
                
        # deduct 2% of the total amount as payment gateway charges
        total -= (total * 0.02)
        return total


# ================= FLAMES TEAMS ======================

class FlamesTeam(models.Model):
    name = models.CharField(max_length=100)
    team_leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_flames_teams', null=True, blank=True)
    course = models.ForeignKey(FlamesCourse, on_delete=models.CASCADE, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)
    is_auto_created = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default="Pending", 
                              choices=[("Pending", "Pending"), 
                                      ("Active", "Active"), 
                                      ("Completed", "Completed")])
    
    def __str__(self):
        return f"{self.name} - {self.course.title}"

# ================= FLAMES TEAM MEMBERS ======================

class FlamesTeamMember(models.Model):
    member = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='flames_team_memberships')
    
    team = models.ForeignKey(FlamesTeam, on_delete=models.CASCADE, related_name='members')
    
    is_leader = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.team.name} - {self.member.first_name}"


# ======================== SESSION MODEL ========================

class Session(models.Model):
    title = models.CharField(max_length=200)
    joining_link = models.URLField(help_text="Link to join the session")
    
    course = models.ForeignKey(FlamesCourse, on_delete=models.CASCADE, related_name='sessions')

    recording_url = models.URLField(blank=True, null=True, help_text="URL to the session recording")

    start_datetime = models.DateTimeField(help_text="Start date and time of the session")
    end_datetime = models.DateTimeField(help_text="End date and time of the session", blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def is_upcoming(self):
        """Check if the session is upcoming based on the start date and time."""
        from django.utils import timezone
        return self.start_datetime > timezone.now()
    
    def is_past(self):
        """Check if the session is past based on the end date and time."""
        from django.utils import timezone
        return self.end_datetime < timezone.now()
    
    def is_live(self):
        """Check if the session is currently live based on the start and end date and time."""
        from django.utils import timezone
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime
    

    def get_status(self):
        """Get the status of the session."""
        if self.is_upcoming():
            return "Upcoming"
        elif self.is_live():
            return "Live"
        elif self.is_past():
            return "Finished"
        else:
            return "Unknown"
        
    def get_status_color(self):
        """Get the color associated with the session status."""
        if self.is_upcoming():
            return "warning"
        elif self.is_live():
            return "success"
        elif self.is_past():
            return "secondary"
        else:
            return "dark"
        
    # set the end time automatically to 1 hour after the start time if not provided
    def save(self, *args, **kwargs):
        if not self.end_datetime:
            if isinstance(self.start_datetime, str):
                from django.utils.dateparse import parse_datetime
                self.start_datetime = parse_datetime(self.start_datetime)

            self.end_datetime = self.start_datetime + timedelta(hours=1)
        super(Session, self).save(*args, **kwargs)
    
    class Meta:
        ordering = ['-start_datetime']
        verbose_name = "Session"
        verbose_name_plural = "Sessions"
    
    def __str__(self):
        return f"{self.title} - {self.course.title}"