from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from student.models import Course, CourseSheet, Assignment
from practice.models import TestCase, DriverCode
from accounts.models import CustomUser


class InstructorSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


# ====================================================
# Course
# ====================================================

class CourseAdminSerializer(serializers.ModelSerializer):
    instructor_names = serializers.SerializerMethodField(read_only=True)
    instructors = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='instructor'),
        many=True,
        required=False
    )
    thumbnail = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Course
        fields = [
            'id', 'name', 'description', 'slug', 'thumbnail',
            'instructors', 'instructor_names', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']

    def get_instructor_names(self, obj):
        return obj.get_instructor_names()

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.thumbnail:
            request = self.context.get('request')
            if request:
                data['thumbnail'] = request.build_absolute_uri(instance.thumbnail.url)
            else:
                data['thumbnail'] = instance.thumbnail.url
        else:
            data['thumbnail'] = None
        return data


# ====================================================
# CourseSheet
# ====================================================

class CourseSheetAdminSerializer(serializers.ModelSerializer):
    course_ids = serializers.SerializerMethodField(read_only=True)
    thumbnail = serializers.ImageField(required=False, allow_null=True)
    assignments_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CourseSheet
        fields = [
            'id', 'name', 'description', 'slug', 'thumbnail',
            'is_enabled', 'is_approved', 'course_ids', 'assignments_count',
        ]
        read_only_fields = ['slug']

    def get_course_ids(self, obj):
        return list(obj.course.values_list('id', flat=True))

    def get_assignments_count(self, obj):
        return obj.assignments.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.thumbnail:
            request = self.context.get('request')
            if request:
                data['thumbnail'] = request.build_absolute_uri(instance.thumbnail.url)
            else:
                data['thumbnail'] = instance.thumbnail.url
        else:
            data['thumbnail'] = None
        return data


# ====================================================
# Assignment
# ====================================================

class AssignmentAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'assignment_type',
            'due_date', 'max_score', 'status', 'is_active',
            'is_tutorial', 'content', 'tutorial_link',
            'instructions', 'allow_late_submission', 'late_penalty_per_day',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


# ====================================================
# TestCase
# ====================================================

class TestCaseAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ['id', 'input_data', 'expected_output', 'explaination', 'is_sample']


# ====================================================
# DriverCode
# ====================================================

LANGUAGE_NAMES = {
    71: 'Python',
    50: 'C',
    54: 'C++',
    62: 'Java',
}

class DriverCodeAdminSerializer(serializers.ModelSerializer):
    language_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DriverCode
        fields = [
            'id', 'language_id', 'language_name',
            'visible_driver_code', 'complete_driver_code',
        ]

    def get_language_name(self, obj):
        return LANGUAGE_NAMES.get(obj.language_id, f'Language {obj.language_id}')
