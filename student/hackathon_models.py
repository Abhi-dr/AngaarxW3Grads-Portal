from django.db import models
from django.utils import timezone
from accounts.models import Student


class HackathonTeam(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    leader = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='led_teams')
    members_limit = models.PositiveIntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    required_skills = models.JSONField(default=list)
    
    def __str__(self):
        return self.name
    
    def current_members_count(self):
        return self.members.count() + 1  # +1 for the leader
    
    def is_full(self):
        return self.current_members_count() >= self.members_limit
    
    def can_join(self):
        return self.status == 'open' and not self.is_full()


class TeamMember(models.Model):
    team = models.ForeignKey(HackathonTeam, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='team_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('team', 'student')
    
    def __str__(self):
        return f"{self.student.username} in {self.team.name}"


class JoinRequest(models.Model):
    team = models.ForeignKey(HackathonTeam, on_delete=models.CASCADE, related_name='join_requests')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='team_requests')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        unique_together = ('team', 'student', 'status')
    
    def __str__(self):
        return f"{self.student.username} requesting to join {self.team.name}"


class TeamInvite(models.Model):
    team = models.ForeignKey(HackathonTeam, on_delete=models.CASCADE, related_name='team_invites')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='team_invites')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        unique_together = ('team', 'student', 'status')
    
    def __str__(self):
        return f"Invite from {self.team.name} to {self.student.user.first_name}"
