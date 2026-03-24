from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from student.api.permissions import IsStudent
from student.api.serializers.student_serializers import StudentProfileSerializer, NotificationSerializer
from student.models import Notification
from practice.models import Batch, Sheet
from practice.models import Submission, MCQSubmission, POD
from student.api.serializers.sheet_serializers import PODSerializer
from django.utils import timezone
from datetime import datetime

class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]
    
    def get(self, request):
        serializer = StudentProfileSerializer(request.user)
        return Response(serializer.data)

class StudentDashboardView(APIView):
    """
    Returns dashboard overview data: active notifications, total stats, next questions, and POD.
    """
    permission_classes = [IsAuthenticated, IsStudent]
    
    def get(self, request):
        student = request.user
        
        # 1. Notifications
        notifications = Notification.objects.filter(
            expiration_date__gt=timezone.now(),
            is_alert=True,
        ).exclude(title__startswith='Approval Request:')
        notif_serializer = NotificationSerializer(notifications, many=True)
        
        # 2. Get enrolled batches and sheets
        enrolled_batches = Batch.objects.filter(
            enrollment_requests__student=student,
            enrollment_requests__status='Accepted'
        )
        
        enrolled_sheets = Sheet.objects.filter(
            batches__in=enrolled_batches,
            is_approved=True,
            is_enabled=True
        ).distinct()
        
        # 3. Calculate sheet statistics
        total_questions_in_sheets = 0
        total_questions_solved_in_sheets = 0
        next_questions = []
        
        for sheet in enrolled_sheets:
            enabled_questions = sheet.get_enabled_questions_for_user(student)
            total_questions_in_sheets += len(enabled_questions)
            
            # Find the next question for this sheet
            next_question_found = False
            
            if sheet.sheet_type == "MCQ":
                answered_questions = set(MCQSubmission.objects.filter(
                    student=student, 
                    question__in=enabled_questions,
                    is_correct=True
                ).values_list('question_id', flat=True))
                
                total_questions_solved_in_sheets += len(answered_questions)
                
                for question in enabled_questions:
                    if question.id not in answered_questions:
                        next_questions.append({
                            'id': question.id,
                            'title': question.question_text[:50],
                            'slug': question.slug,
                            'difficulty': question.difficulty_level,
                            'sheet_slug': sheet.slug,
                            'sheet_name': sheet.name,
                            'type': 'MCQ'
                        })
                        next_question_found = True
                        break
            else:
                solved_questions = set(Submission.objects.filter(
                    user=student,
                    question__in=enabled_questions,
                    status='Accepted'
                ).values_list('question_id', flat=True))
                
                total_questions_solved_in_sheets += len(solved_questions)
                
                for question in enabled_questions:
                    if question.id not in solved_questions:
                        next_questions.append({
                            'id': question.id,
                            'title': question.title,
                            'slug': question.slug,
                            'difficulty': question.difficulty_level,
                            'sheet_slug': sheet.slug,
                            'sheet_name': sheet.name,
                            'type': 'Coding'
                        })
                        next_question_found = True
                        break
                        
        questions_completion_percentage = int((total_questions_solved_in_sheets / total_questions_in_sheets) * 100) if total_questions_in_sheets > 0 else 0
        questions_left = total_questions_in_sheets - total_questions_solved_in_sheets
        
        # 4. Today's POD
        pod_data = None
        if enrolled_batches.exists():
            pod = POD.objects.filter(
                batch__in=enrolled_batches,
                date=datetime.now().date()
            ).first()
            if pod:
                pod_data = PODSerializer(pod).data
                
        # 5. Check birthday
        is_birthday = False
        try:
            if student.dob and student.dob.day == timezone.now().day and student.dob.month == timezone.now().month:
                is_birthday = True
        except Exception:
            pass

        return Response({
            "notifications": notif_serializer.data,
            "stats": {
                "total_sheets": enrolled_sheets.count(),
                "total_questions": total_questions_in_sheets,
                "total_solved": total_questions_solved_in_sheets,
                "completion_percentage": questions_completion_percentage,
                "questions_left": questions_left,
            },
            "next_questions": next_questions[:3],
            "pod": pod_data,
            "is_birthday": is_birthday
        })
