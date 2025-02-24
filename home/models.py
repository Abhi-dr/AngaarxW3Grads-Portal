from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
    
# ======================= JOB ARTICLE MODEL ======================

class Article(models.Model):
    title = models.CharField(max_length=100)
    content = RichTextUploadingField()
    thumbnail = models.ImageField(upload_to="thumbnails/")
    
    slug = models.SlugField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        
    def __str__(self):
        return self.title
    
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