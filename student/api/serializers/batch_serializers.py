from rest_framework import serializers
from practice.models import Batch
from student.models import Course

class BatchListSerializer(serializers.ModelSerializer):
    enrollment_status = serializers.CharField(read_only=True, default='Not Enrolled')
    
    class Meta:
        model = Batch # normal courses
        fields = ['id', 'name', 'slug', 'thumbnail', 'required_fields', 'enrollment_status']

class CourseListSerializer(serializers.ModelSerializer):
    registration_status = serializers.CharField(read_only=True, default='Not Enrolled')
    instructor_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Course # JOVAC
        fields = ['id', 'name', 'slug', 'thumbnail', 'registration_status', 'instructor_names']
        
    def get_instructor_names(self, obj):
        return obj.get_instructor_names()
