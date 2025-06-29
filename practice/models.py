from django.db import models
from datetime import datetime, timedelta
from django.utils.timezone import now

from accounts.models import Student, Instructor

# ============================== BATCH ======================================


class Batch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to='batches/thumbnails/', blank=True, null=True)
    students = models.ManyToManyField(Student, related_name="batches", through="EnrollmentRequest")
    
    required_fields = models.JSONField(default=list, blank=True)

    
    slug = models.SlugField(unique=True, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            text = ""
        
            for word in self.name.split():
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
            while Batch.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug
        super(Batch, self).save(*args, **kwargs)
        
        
    def get_today_pod_for_batch(self):
        return self.pods.filter(date=datetime.now().date()).first()


# ============================== ENROLLMENT REQUEST =========================


class EnrollmentRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollment_requests")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="enrollment_requests")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    request_date = models.DateTimeField(auto_now_add=True)
    
    additional_data = models.JSONField(default=dict, blank=True)


    class Meta:
        unique_together = ('student', 'batch')  # Prevent duplicate requests

    def __str__(self):
        return f"{self.student.first_name} - {self.batch.name} ({self.status})"


# ============================== SHEET ======================================


class Sheet(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    slug = models.SlugField(unique=True, blank=True, null=True)
    
    thumbnail = models.ImageField(upload_to='sheets/thumbnails/', blank=True, null=True)
    batches = models.ManyToManyField(Batch, related_name="sheets", blank=True)
    
    created_by = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name="sheets", blank=True, null=True)
    
    custom_order = models.JSONField(default=dict)  # Store order as {question_id: position}
    
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Field to check if the sheet will be treated as a STORYLINE
    is_sequential = models.BooleanField(default=False)
    
    # Is sheet enabled or not
    is_enabled = models.BooleanField(default=True)
    
    is_approved = models.BooleanField(default=False)
    
    def is_active(self):
        """Checks if the sheet is active based on the current time."""
        return self.is_enabled and (self.start_time <= now() <= self.end_time)
    
    def get_enabled_questions_for_user(self, user):
        """
        Returns the questions that should be enabled for the user based on sequential logic.
        """
        if not self.is_sequential:
            return self.get_ordered_questions()  # Return all questions if not sequential
        
        # Get all questions sorted by their custom order or default order
        questions = self.get_ordered_questions()
        solved_questions = Submission.objects.filter(
            user=user,
            question__in=questions,
            status='Accepted'
        ).values('question').distinct()  # Get questions solved by the user

        # Enable only the solved questions and the first unsolved question
        enabled_questions = questions[:len(solved_questions) + 1]

        return enabled_questions
    
    def get_ordered_questions(self):
        # Get questions in the custom order
        questions = list(self.questions.filter(is_approved=True))
        if self.custom_order:
            questions.sort(key=lambda q: self.custom_order.get(str(q.id), 0))
        return questions
    
    def get_next_question(self, current_question):
        questions = self.get_ordered_questions()
        current_index = questions.index(current_question)
        
        if current_index + 1 < len(questions):
            return questions[current_index + 1]
        return None

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Sheet'
        verbose_name_plural = 'Sheets'
        
    def get_total_questions(self):
        return self.questions.filter(is_approved=True).count()
    
    def get_solved_questions(self, student):
        return Submission.objects.filter(
            user=student,
            question__in=self.questions.all(),
            status='Accepted'
        ).values('question').distinct().count()
        
    def get_progress(self, student):
        total_questions = self.questions.count()
        completed_questions = Submission.objects.filter(
            user=student,
            question__in=self.questions.all(),
            status='Accepted'
        ).values('question').distinct().count()

        if total_questions == 0:
            return 0
        return (completed_questions / total_questions) * 100
        
    def save(self, *args, **kwargs):
        
        if not self.slug:
            text = ""
        
            for word in self.name.split():
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
            while Sheet.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug
        
        super(Sheet, self).save(*args, **kwargs)
        

# ============================== QUESTION MODEL =============================


class Question(models.Model):
    sheets = models.ManyToManyField(Sheet, related_name="questions", blank=True)
    
    title = models.CharField(max_length=255)
    scenario = models.TextField(blank=True, null=True)
    description = models.TextField()
    constraints = models.TextField(blank=True, null=True)
    
    input_format = models.TextField(blank=True, null=True)
    output_format = models.TextField(blank=True, null=True)
        
    cpu_time_limit = models.FloatField(default=1, blank=True, null=True)
    memory_limit = models.PositiveIntegerField(default=256, blank=True, null=True)
    
    show_complete_driver_code = models.BooleanField(default=False)  # New field
    
    
    difficulty_level = models.CharField(max_length=50, choices=[
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ])
    
    youtube_link = models.URLField(blank=True, null=True)
    
    position = models.PositiveIntegerField(default=0)
    
    hint = models.TextField(blank=True, null=True)
    
    slug = models.SlugField(blank=True, null=True)
    
    added_by = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="questions", blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    
    # Parent ID Concept
    parent_id = models.IntegerField(default=-1)  # -1 means original question

    class Meta:
        indexes = [
        models.Index(fields=['position']),
    ]
        ordering = ['position']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    def __str__(self):
        return f"{self.title} (Position: {self.position})"
    
    def get_difficulty_level_color(self):
        if self.difficulty_level == 'Easy':
            return 'success'
        elif self.difficulty_level == 'Medium':
            return 'warning'
        elif self.difficulty_level == 'Hard':
            return 'danger'

    def is_solved_by_user(self, user):
        return self.submissions.filter(user=user, status='Accepted').exists()
    
    def get_user_status(self, user):
        if self.submissions.filter(user=user, status='Accepted').exists():
            return 'Accepted'
        
        elif self.submissions.filter(user=user).exists():
            return self.submissions.filter(user=user).last().status
    
    def get_status_color(self, user):
        if self.get_user_status(user) == 'Accepted':
            return 'success'
        elif self.get_user_status(user) == 'Pending':
            return 'secondary'
        elif self.get_user_status(user) == 'Wrong Answer':
            return 'danger'
        elif self.get_user_status(user) == 'Runtime Error':
            return 'warning'
        elif self.get_user_status(user) == 'Time Limit Exceeded':
            return 'info'
        elif self.get_user_status(user) == 'Compilation Error':
            return 'dark'
    
    def how_many_users_solved(self):
        # count only once by one user
        return self.submissions.filter(status='Accepted').distinct().count()
    
    def how_many_users_attempted(self):
        return self.submissions.count()
    
    def get_approved_status(self):
        if self.is_approved:
            return 'Approved'        
        else:
            return 'Pending'
    
    def how_many_users_solved_today(self):
        start_of_day = now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        result = self.submissions.filter(
            submitted_at__gte=start_of_day,
            submitted_at__lt=end_of_day,
            status='Accepted'
        ).count()
        return result

    def how_many_users_attempted_today(self):
        start_of_day = now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        result = self.submissions.filter(
            submitted_at__gte=start_of_day,
            submitted_at__lt=end_of_day
        ).count()
        return result
    
    def get_approved_status_color(self):
        if self.is_approved:
            return 'success'
        else:
            return 'info'

    def save(self, *args, **kwargs):
        # Auto-assign position if not already set
        if not self.position:
            self.position = Question.objects.count() + 1
        
        if self.position != self.pk:  # If the question is being moved
            Question.objects.filter(position__gte=self.position).update(position=models.F('position') + 1)
            
                
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
            while Question.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        
        super().save(*args, **kwargs)
        
    
# ============================== DRIVER CODE ================================


class DriverCode(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='driver_codes')
    language_id = models.IntegerField(default=0)
    visible_driver_code = models.TextField()  # Code displayed to the user
    complete_driver_code = models.TextField()
    
    LANGUAGE_CHOICES = {
        71: 'Python',
        50: 'C',
        54: 'C++',
        62: 'Java',
    }
    
    class Meta:
        indexes = [
        models.Index(fields=['question', 'language_id']),
    ]
    unique_together = ('question', 'language_id')  # Prevent duplicate driver codes
    
    def __str__(self):
        return f"Driver Code for {self.question.title}"
    
    def get_name_through_id(self):
        return dict(self.LANGUAGE_CHOICES).get(self.language_id)


# ============================== TEST CASE ==================================


class TestCase(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField()
    expected_output = models.TextField()
    explaination = models.TextField(blank=True, null=True)
    is_sample = models.BooleanField(default=False)  # For sample test cases

    def __str__(self):
        return f"Test Case for {self.question.title}"
    
    class Meta:
        indexes = [
        models.Index(fields=['question']),
    ]      


# ============================== SUBMISSION =================================


class Submission(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Wrong Answer', 'Wrong Answer'),
        ('Runtime Error', 'Runtime Error'),
        ('Time Limit Exceeded', 'Time Limit Exceeded'),
        ('Compilation Error', 'Compilation Error'),
    ]
    
    user = models.ForeignKey(Student, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="submissions")
    code = models.TextField()
    language = models.CharField(max_length=20)  # E.g., 'python', 'java', 'cpp'
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    score = models.PositiveIntegerField(default=0)  # Score based on the test cases passed
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def get_langauge_name_through_id(self):
        return dict(self.LANGUAGE_CHOICES).get(self.language)
    
    def get_todays_submissions(self, user):
        return self.submissions.filter(user=user, submitted_at__date=datetime.now().date())
    
    @classmethod
    def get_todays_total_submissions(cls):
        today = now().date()
        return cls.objects.filter(submitted_at__date=today).count()
    
    def __str__(self):
        return f"{self.user.username} - {self.question.title} - {self.status}"
    

# ================================= POD =====================================


class POD(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="pods")
    date = models.DateField(default=datetime.now)
    
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, related_name="pods", null=True, blank=True)

    def __str__(self):
        return f"{self.question.title} - {self.date}"
    
    def is_solved_by_user(self, user):
        return self.question.submissions.filter(user=user, status='Accepted').exists()


# ============================== STREAK =====================================


class Streak(models.Model):
    user = models.ForeignKey(Student, on_delete=models.CASCADE)
    current_streak = models.PositiveIntegerField(default=1)  # Current streak of consecutive submissions
    last_submission_date = models.DateField(null=True, blank=True)

    def update_streak(self):
        today = datetime.now().date()
        
        # Check if the last submission was yesterday
        if self.last_submission_date == today - timedelta(days=1):
            self.current_streak += 1
        elif self.last_submission_date != today:
            self.current_streak = 1  # Reset if it's not consecutive

        self.last_submission_date = today
        self.save()

    def can_restore_streak(self):
        today = datetime.now().date()
        return (
            self.last_submission_date == today - timedelta(days=2)
            and not self.restored_today
        )

    def restore_streak(self):
        """Restore the streak to the previous day."""
        if self.can_restore_streak():
            self.last_submission_date = datetime.now().date()
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.user.username} - {self.current_streak} day streak"
    

# ============================== SOLUTION ===================================


class Solution(models.Model):
    
    LANGUAGE_CHOICES = [
        ('Python', 'Python'),
        ("C", "C"),
        ('C++', 'C++'),
        ('Java', 'Java'),
    ]
    
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="solutions")
    language_id = models.IntegerField(default=0)
    code = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def get_langauge_name_through_id(self):
        return dict(self.LANGUAGE_CHOICES).get(self.language)

    def __str__(self):
        return f"{self.user.username} - {self.question.title}"


# ============================== Recommended Question =======================


class RecommendedQuestions(models.Model):

    platform_choices = [
        ('LeetCode', 'LeetCode'),
        ('HackerRank', 'HackerRank'),
        ('GeeksForGeeks', 'GeeksForGeeks')
    ]

    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="recommended_questions") 
    title = models.CharField(max_length=255)
    link = models.URLField()
    platform = models.CharField(max_length=50, choices=platform_choices)
    
