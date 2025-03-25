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

# ========================== FLAMES ===========================

class FlamesCourse(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=255)
    description = models.TextField()
    
    instructor = models.CharField(max_length=200)
    
    
    what_you_will_learn = models.TextField(help_text="Enter points separated by new lines")
    
    roadmap = models.TextField(help_text="Course roadmap details")
    
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True)
    
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    icon_class = models.CharField(max_length=50, help_text="Font Awesome icon class")
    icon_color = models.CharField(max_length=200, help_text="Color for the course card")
    button_color = models.CharField(max_length=200, help_text="Color for the course button")
    
    def __str__(self):
        return self.title
    
    def get_learning_points(self):
        """Return what_you_will_learn as a list of points"""
        return self.what_you_will_learn.strip().split('\n')

class FlamesCourseTestimonial(models.Model):
    course = models.ForeignKey(FlamesCourse, on_delete=models.CASCADE, related_name='testimonials')
    student_name = models.CharField(max_length=100)
    student_image = models.ImageField(upload_to="flames/testimonials/", blank=True, null=True)
    content = models.TextField()
    rating = models.IntegerField(default=5, choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    
    def __str__(self):
        return f"Testimonial by {self.student_name} for {self.course.title}"

class FlamesRegistration(models.Model):
    course = models.ForeignKey(FlamesCourse, on_delete=models.CASCADE, related_name='registrations')
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    contact_number = models.CharField(max_length=15)
    college = models.CharField(max_length=200)
    year = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.course.title}"
