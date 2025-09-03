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


class SiteSettings(models.Model):
    maintenance_mode = models.BooleanField(default=False)

    def __str__(self):
        return "Site Settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # Always keep the ID as 1 (singleton)
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
