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

