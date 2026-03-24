from rest_framework import serializers
from practice.models import Batch, Sheet, Question, MCQQuestion

class BatchInstructorSerializer(serializers.ModelSerializer):
    """
    Read-only Serializer for Instructors to list Batches.
    Instructors generally don't create or modify batches directly without admin review.
    """
    
    class Meta:
        model = Batch
        fields = ['id', 'name', 'slug', 'description', 'thumbnail', 'required_fields', 'is_active']
        read_only_fields = fields # All read-only


class SheetSummaryInstructorSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()

    class Meta:
        model = Sheet
        fields = ['id', 'name', 'slug', 'thumbnail', 'is_enabled', 'sheet_type', 'total_questions']

    def get_total_questions(self, obj):
        return obj.get_total_questions()


class BatchDetailInstructorSerializer(BatchInstructorSerializer):
    sheets = serializers.SerializerMethodField()

    class Meta(BatchInstructorSerializer.Meta):
        fields = BatchInstructorSerializer.Meta.fields + ['sheets']

    def get_sheets(self, obj):
        sheets = obj.sheets.all().order_by('-id')
        return SheetSummaryInstructorSerializer(sheets, many=True, context=self.context).data


class QuestionLiteInstructorSerializer(serializers.ModelSerializer):
    difficulty_level_color = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'slug', 'title', 'description', 'difficulty_level', 'difficulty_level_color']

    def get_difficulty_level_color(self, obj):
        return obj.get_difficulty_level_color()


class MCQQuestionLiteInstructorSerializer(serializers.ModelSerializer):
    difficulty_level_color = serializers.SerializerMethodField()

    class Meta:
        model = MCQQuestion
        fields = ['id', 'slug', 'question_text', 'difficulty_level', 'difficulty_level_color']

    def get_difficulty_level_color(self, obj):
        return obj.get_difficulty_level_color()


class SheetDetailInstructorSerializer(serializers.ModelSerializer):
    coding_questions = serializers.SerializerMethodField()
    mcq_questions = serializers.SerializerMethodField()

    class Meta:
        model = Sheet
        fields = [
            'id', 'name', 'slug', 'sheet_type', 'is_enabled',
            'coding_questions', 'mcq_questions'
        ]

    def get_coding_questions(self, obj):
        questions = obj.questions.filter(is_approved=True)
        return QuestionLiteInstructorSerializer(questions, many=True, context=self.context).data

    def get_mcq_questions(self, obj):
        questions = obj.mcq_questions.all()
        return MCQQuestionLiteInstructorSerializer(questions, many=True, context=self.context).data
