from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from student.api.permissions import IsStudent
from practice.models import Sheet, Question, MCQQuestion, Submission, MCQSubmission, Batch, EnrollmentRequest
from student.api.serializers.sheet_serializers import SheetListSerializer, QuestionListSerializer, MCQQuestionListSerializer
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class SheetDetailView(APIView, StandardResultsSetPagination):
    """
    Returns sheet data and a paginated list of enabled questions for the student.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, slug):
        student = request.user
        sheet = get_object_or_404(Sheet, slug=slug, is_approved=True)

        print(sheet.get_progress(student))
        
        if not sheet.is_enabled:
            return Response({"error": "This sheet is not disabled."}, status=403)

        all_questions = sheet.get_ordered_questions()
        enabled_questions = sheet.get_enabled_questions_for_user(student)
        enabled_ids = {q.id for q in enabled_questions}
        
        # Fetch submissions to annotate status locally instead of doing N+1
        if sheet.sheet_type == "MCQ":
            submissions = MCQSubmission.objects.filter(student=student, question__in=all_questions)
            status_map = {sub.question_id: ('Accepted' if sub.is_correct else 'Wrong Answer') for sub in submissions}
            
            # DRF pagination on list
            page = self.paginate_queryset(list(all_questions), request, view=self)
            
            # Inject statuses and enabled flag
            for q in page:
                q.status = status_map.get(q.id, 'Pending')
                q.is_enabled = q.id in enabled_ids
                
            serialized_questions = MCQQuestionListSerializer(page, many=True).data
        else:
            submissions = Submission.objects.filter(user=student, question__in=all_questions)
            status_map = {}
            for sub in submissions:
                if sub.status == 'Accepted' or sub.question_id not in status_map:
                    status_map[sub.question_id] = sub.status
                    
            page = self.paginate_queryset(list(all_questions), request, view=self)
            
            for q in page:
                q.status = status_map.get(q.id, 'Pending')
                q.is_enabled = q.id in enabled_ids
                if q.status == 'Accepted':
                    q.color = 'success'
                elif q.status == 'Pending':
                    q.color = 'secondary'
                elif q.status == 'Wrong Answer':
                    q.color = 'danger'
                else:
                    q.color = 'warning'
                    
            serialized_questions = QuestionListSerializer(page, many=True).data

        return self.get_paginated_response({
            "sheet": SheetListSerializer(sheet).data,
            "questions": serialized_questions
        })

class QuestionReadOnlyView(APIView):
    """
    Read-only data for a single question. Useful for side panels or previews without
    triggering the submission environment.
    """
    permission_classes = [IsAuthenticated, IsStudent]
    
    def get(self, request, slug):
        # Could be MCQ or standard Question. Differentiate based on what resolves.
        question = Question.objects.filter(slug=slug, is_approved=True).prefetch_related('test_cases', 'images').first()
        if question:
            sample_tcs = question.test_cases.filter(is_sample=True)
            samples = []
            for tc in sample_tcs:
                samples.append({
                    "input_data": tc.input_data,
                    "expected_output": tc.expected_output,
                    "explaination": tc.explaination
                })
                
            images = []
            for img in question.images.all():
                images.append({
                    "url": img.image.url if img.image else None,
                    "caption": img.caption
                })
                
            # Manually construct descriptive JSON
            return Response({
                "type": "Coding",
                "id": question.id,
                "title": question.title,
                "scenario": question.scenario,
                "description": question.description,
                "constraints": question.constraints,
                "input_format": question.input_format,
                "output_format": question.output_format,
                "difficulty_level": question.difficulty_level,
                "difficulty_color": question.get_difficulty_level_color(),
                "youtube_link": question.youtube_link,
                "samples": samples,
                "images": images,
                "hint_available": bool(question.hint)
            })
            
        mcq_question = get_object_or_404(MCQQuestion, slug=slug, is_approved=True)
        return Response({
            "type": "MCQ",
            "id": mcq_question.id,
            "question_text": mcq_question.question_text,
            "option_a": mcq_question.option_a,
            "option_b": mcq_question.option_b,
            "option_c": mcq_question.option_c,
            "option_d": mcq_question.option_d,
            "difficulty_level": mcq_question.difficulty_level,
        })
