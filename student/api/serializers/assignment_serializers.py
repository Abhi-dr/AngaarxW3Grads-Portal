from rest_framework import serializers
from urllib.parse import parse_qs, urlparse

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


class AssignmentDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single assignment/tutorial with all fields
    """
    due_date_formatted = serializers.SerializerMethodField()
    due_time_formatted = serializers.SerializerMethodField()
    downloadable_file_url = serializers.SerializerMethodField()
    youtube_video_id = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    course_slug = serializers.SerializerMethodField()
    instructor_names = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'content', 'assignment_type',
            'due_date', 'due_date_formatted', 'due_time_formatted',
            'is_tutorial', 'tutorial_link', 'youtube_video_id',
            'downloadable_file_url', 'is_overdue',
            'course_name', 'course_slug', 'instructor_names',
            'created_at', 'updated_at'
        ]
    
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
    
    def get_youtube_video_id(self, obj):
        if obj.tutorial_link:
            parsed = urlparse(obj.tutorial_link)
            normalized_netloc = parsed.netloc.replace('www.', '')

            if normalized_netloc == 'youtu.be':
                return parsed.path.lstrip('/') or None

            if normalized_netloc in {'youtube.com', 'm.youtube.com', 'youtube-nocookie.com'}:
                query_video_id = parse_qs(parsed.query).get('v', [None])[0]
                if query_video_id:
                    return query_video_id

                path_parts = [part for part in parsed.path.split('/') if part]
                if len(path_parts) >= 2 and path_parts[0] in {'embed', 'shorts', 'live'}:
                    return path_parts[1]

        return None
    
    def get_course_name(self, obj):
        if obj.course:
            return obj.course.name
        return None
    
    def get_course_slug(self, obj):
        if obj.course:
            return obj.course.slug
        return None
    
    def get_instructor_names(self, obj):
        if obj.course:
            return obj.course.get_instructor_names()
        return None
    
    def get_is_overdue(self, obj):
        return obj.is_overdue


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'student', 'submitted_at', 'status']
