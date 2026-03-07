from rest_framework import serializers
from practice.models import Sheet, Question, MCQQuestion, POD

class SheetListSerializer(serializers.ModelSerializer):
    total_questions = serializers.SerializerMethodField()
    
    class Meta:
        model = Sheet
        fields = ['id', 'name', 'slug', 'thumbnail', 'description', 'sheet_type', 'is_sequential', 'total_questions', 'is_enabled']
        
    def get_total_questions(self, obj):
        return obj.get_total_questions()

class QuestionListSerializer(serializers.ModelSerializer):
    difficulty_color = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True, required=False) # Will be annotated in the queryset or manually set
    color = serializers.CharField(read_only=True, required=False) # Will be derived in views
    is_enabled = serializers.BooleanField(read_only=True, required=False) # Set manually in views
    tag_list = serializers.ListField(child=serializers.CharField(), source='tags.all', read_only=True, required=False)
    
    class Meta:
        model = Question
        fields = ['id', 'title', 'slug', 'difficulty_level', 'difficulty_color', 'youtube_link', 'position', 'status', 'color', 'is_enabled', 'tag_list']
        
    def get_difficulty_color(self, obj):
        return obj.get_difficulty_level_color()

class MCQQuestionListSerializer(serializers.ModelSerializer):
    difficulty_color = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True, required=False) 
    is_enabled = serializers.BooleanField(read_only=True, required=False)
    tag_list = serializers.ListField(child=serializers.CharField(), source='tags.all', read_only=True, required=False)
    
    class Meta:
        model = MCQQuestion
        fields = ['id', 'question_text', 'slug', 'difficulty_level', 'difficulty_color', 'status', 'is_enabled', 'tag_list']
        
    def get_difficulty_color(self, obj):
        return obj.get_difficulty_level_color()

# KOI KAAM NAHI H ISSE ABHI

class PODSerializer(serializers.ModelSerializer):
    question_title = serializers.CharField(source='question.title', read_only=True)
    question_slug = serializers.CharField(source='question.slug', read_only=True)
    question_difficulty = serializers.CharField(source='question.difficulty_level', read_only=True)
    
    class Meta:
        model = POD
        fields = ['id', 'date', 'question_title', 'question_slug', 'question_difficulty']
