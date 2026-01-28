from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import hashlib
import secrets

# ================================================= ADMINISTRATOR ==========================================

class Administrator(User):
    profile_pic = models.ImageField(
        upload_to="teacher_profile", blank=True, null=True, default="/student_profile/default.jpg")

    gender = models.CharField(max_length=19)
    linkedin_id = models.URLField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    
    college = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Administrators"
        verbose_name = "Administrator"
         
    def __str__(self):
        return self.username


# ================================================= Instructor ==========================================

class Instructor(User):
    profile_pic = models.ImageField(
        upload_to="teacher_profile", blank=True, null=True, default="/student_profile/default.jpg")

    gender = models.CharField(max_length=19)
    linkedin_id = models.URLField(blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    
    college = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Instructors"
        verbose_name = "Instructor"
         
    def __str__(self):
        return self.username
    

# ======================================= Student ==========================================

class Student(User):
    mobile_number = models.CharField(max_length=10)
    gender = models.CharField(max_length=10)
    college = models.CharField(max_length=100, blank=True, null=True)
    
    dob = models.DateField(blank=True, null=True)
    is_changed_password = models.BooleanField(default=False)
    
    profile_pic = models.ImageField(
        upload_to="student_profile/", blank=True, null=True, default="/student_profile/default.jpg")
    
    linkedin_id = models.URLField(blank=True, null=True)
    github_id = models.URLField(blank=True, null=True)
    
    coins = models.IntegerField(default=100)
    
    # courses = models.ManyToManyField(Course, blank=True)
    
    def __str__(self):
        return self.username
    
    def get_profile_score(self):
        score = 30
        
        if self.dob:
            score += 20
        
        if self.linkedin_id:
            score += 30
        
        if self.github_id:
            score += 20
        
        return score

    class Meta:
        verbose_name_plural = "Students"
        verbose_name = "Student"

    
    # def get_attendance_percentage(self):
    #     total = ScrumMeeting.objects.count()
    #     attended = Attendance.objects.filter(student=self, attended=True).count()
    #     return int((attended/total)*100)
        
    # def save(self, *args, **kwargs):
    #     if not self.pk:
    #         self.is_staff = False
    #         self.set_password('angaarhai')
    #     super().save(*args, **kwargs)


# ===================================== RESET PASSWORD ==========================================

class PasswordResetToken(models.Model):
    user = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='password_reset_tokens')
    token_hash = models.CharField(max_length=64, unique=True)  # Store hashed token
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    @classmethod
    def create_token(cls, user):    
        cls.objects.filter(user=user).delete()  # Remove existing tokens
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


# ===================================== EMAIL VERIFICATION ==========================================

class EmailVerificationToken(models.Model):
    user = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='email_verification_tokens')
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)  # 24 hours validity
        super().save(*args, **kwargs)

    @classmethod
    def create_token(cls, user):
        cls.objects.filter(user=user).delete()  # Remove existing tokens
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

