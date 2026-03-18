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
# Mixed Item
# ====================================================

class CourseSheetMixedItemSerializer(serializers.Serializer):
    item_id = serializers.CharField()
    type = serializers.CharField()
    pk = serializers.IntegerField()
    obj = serializers.SerializerMethodField()
    
    def get_obj(self, instance):
        obj = instance['obj']
        if instance['type'] == 'Assignment':
            return AssignmentAdminSerializer(obj, context=self.context).data
        elif instance['type'] == 'MCQ':
            return {
                'id': obj.id,
                'title': getattr(obj, 'question_text', '')[:100] + ('...' if len(getattr(obj, 'question_text', '')) > 100 else ''),
                'slug': obj.slug,
                'is_approved': obj.is_approved,
                'difficulty_level': obj.difficulty_level,
                'type': 'MCQ'
            }
        elif instance['type'] == 'Coding':
            return {
                'id': obj.id,
                'title': obj.title,
                'slug': obj.slug,
                'is_approved': obj.is_approved,
                'difficulty_level': obj.difficulty_level,
                'type': 'Coding'
            }
        return {}



from practice.models import Question, MCQQuestion

# ====================================================
# MCQQuestion
# ====================================================

class MCQQuestionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCQQuestion
        fields = [
            'id', 'sheet', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d',
            'correct_option', 'explanation', 'tags', 'difficulty_level', 'slug', 'is_approved'
        ]
        read_only_fields = ['slug']
    
    def create(self, validated_data):
        """Ensure is_approved is always True for JOVAC MCQs"""
        validated_data['is_approved'] = True
        return super().create(validated_data)

# ====================================================
# Question (Coding)
# ====================================================

class QuestionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'title', 'scenario', 'description', 'constraints',
            'input_format', 'output_format', 'cpu_time_limit', 'memory_limit',
            'show_complete_driver_code', 'difficulty_level', 'youtube_link',
            'position', 'hint', 'slug', 'is_approved'
        ]
        read_only_fields = ['slug', 'position']

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
