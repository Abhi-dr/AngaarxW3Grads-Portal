from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from accounts.models import Student, Instructor


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
        
