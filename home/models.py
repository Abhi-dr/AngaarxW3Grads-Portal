from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.models import User
    
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