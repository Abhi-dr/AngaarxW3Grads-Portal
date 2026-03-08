from rest_framework import serializers
from student.models import Assignment, AssignmentSubmission


class AssignmentListSerializer(serializers.ModelSerializer):
    is_submitted = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    due_date_formatted = serializers.SerializerMethodField()
    due_time_formatted = serializers.SerializerMethodField()
    downloadable_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'assignment_type', 
            'due_date', 'due_date_formatted', 'due_time_formatted',
            'is_tutorial', 'tutorial_link', 'content',
            'downloadable_file_url', 'is_submitted', 'is_overdue'
        ]
    
    def get_is_submitted(self, obj):
        # This will be set manually in the view
        return getattr(obj, 'is_submitted', False)
    
    def get_is_overdue(self, obj):
        return obj.is_overdue
    
    def get_due_date_formatted(self, obj):
        if obj.due_date:
            return obj.due_date.strftime('%Y-%m-%d')
        return None
    
    def get_due_time_formatted(self, obj):
        if obj.due_date:
            return obj.due_date.strftime('%I:%M %p')
        return None
    
    def get_downloadable_file_url(self, obj):
        if obj.downloadable_file:
            return obj.downloadable_file.url
        return None


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'student', 'submitted_at', 'status']
