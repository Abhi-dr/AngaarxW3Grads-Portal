from django.db import models

class Flames(models.Model):
    name = models.CharField(max_length=100)
    whatsapp_number = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=100)
    college = models.CharField(max_length=100)
    mode = models.CharField(max_length=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
# ======================= JOB ARTICLE MODEL ======================

class Article(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        
    def __str__(self):
        return self.title