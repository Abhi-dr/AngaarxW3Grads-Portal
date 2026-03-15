from datetime import datetime
from django.utils.timezone import now
from django.db.models import Case, When, Value, CharField, Q
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Make sure these import paths match your project structure
from student.api.permissions import IsStudent
from student.models import Notification
from student.api.serializers.batch_serializers import BatchListSerializer
from student.api.serializers.sheet_serializers import SheetListSerializer, PODSerializer

from practice.models import (
    Batch, 
    EnrollmentRequest, 
    Sheet, 
    Question, 
    MCQQuestion, 
    POD, 
    Submission, 
    MCQSubmission
)


class BatchListView(APIView):
    """
    Returns lists of batches organized by enrollment status.
    Mimics the old fetch_my_batch_data JSON response.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        
        # Batch Data — only show active courses to students
        all_batches = Batch.objects.filter(is_active=True).annotate(
            enrollment_status=Case(
                When(enrollment_requests__student=student, enrollment_requests__status='Accepted', then=Value('Accepted')),
                When(enrollment_requests__student=student, enrollment_requests__status='Pending', then=Value('Pending')),
                When(enrollment_requests__student=student, enrollment_requests__status='Rejected', then=Value('Rejected')),
                default=Value('Not Enrolled'),
                output_field=CharField(),
            )
        ).select_related().distinct()

        student_batches = all_batches.filter(enrollment_status='Accepted')
        pending_batches = all_batches.filter(enrollment_status='Pending')
        rejected_batches = all_batches.filter(enrollment_status='Rejected')
        
        other_batches = [
            b for b in all_batches 
            if b.enrollment_status not in ['Accepted', 'Pending', 'Rejected']
        ]

        return Response({
            "success": True,
            "batches": {
                "student_batches": BatchListSerializer(student_batches, many=True).data,
                "pending_batches": BatchListSerializer(pending_batches, many=True).data,
                "rejected_batches": BatchListSerializer(rejected_batches, many=True).data,
                "other_batches": BatchListSerializer(other_batches, many=True).data,
            }
        })


class BatchDetailView(APIView):
    """
    Returns detailed information about a single batch, including its sheets and progress.
    Optimized to eliminate N+1 queries.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, slug):
        student = request.user
        batch = get_object_or_404(Batch, slug=slug)
        
        # Security: check if enrolled
        if not EnrollmentRequest.objects.filter(student=student, batch=batch, status='Accepted').exists():
            return Response({"error": "Not enrolled in this batch."}, status=403)
            
        # 1. Fetch only ACTIVE sheets (Approved, Enabled, and within time limits)
        active_conditions = Q(batches=batch, is_approved=True, is_enabled=True)
        active_conditions &= (Q(start_time__isnull=True) | Q(start_time__lte=now()))
        active_conditions &= (Q(end_time__isnull=True) | Q(end_time__gte=now()))
        
        active_sheets = Sheet.objects.filter(active_conditions).order_by('id')
        
        # 2. Calculate Total Questions globally across all active sheets
        total_coding = Question.objects.filter(
            sheets__in=active_sheets, 
            is_approved=True
        ).distinct().count()
        
        total_mcq = MCQQuestion.objects.filter(
            sheet__in=active_sheets, 
            is_approved=True
        ).distinct().count()
        
        total_questions = total_coding + total_mcq
        
        # 3. Calculate Solved Questions globally
        solved_coding = Submission.objects.filter(
            user=student,
            status='Accepted',
            question__sheets__in=active_sheets,
            question__is_approved=True
        ).values('question').distinct().count()
        
        solved_mcq = MCQSubmission.objects.filter(
            student=student,
            is_correct=True,
            question__sheet__in=active_sheets,
            question__is_approved=True
        ).values('question').distinct().count()
            
        solved_questions = solved_coding + solved_mcq
        
        # 4. Final Math
        progress = (solved_questions / total_questions * 100) if total_questions > 0 else 0
        questions_left = total_questions - solved_questions
        
        # 5. Serialize Sheets
        sheet_data = SheetListSerializer(active_sheets, many=True).data
        
        # 6. POD Data
        pod_data = None
        pod = POD.objects.filter(batch=batch, date=now().date()).first()
        
        if pod:
            pod_serializer = PODSerializer(pod).data
            
            # Check if solved (either Coding or MCQ)
            is_solved = Submission.objects.filter(
                user=student, 
                question_id=pod.question.id, 
                status='Accepted'
            ).exists()
            
            if not is_solved:
                is_solved = MCQSubmission.objects.filter(
                    student=student, 
                    question_id=pod.question.id, 
                    is_correct=True
                ).exists()
                
            pod_serializer['is_solved_by_user'] = is_solved
            pod_data = pod_serializer
        
        return Response({
            "batch": BatchListSerializer(batch).data,
            "total_questions": total_questions,
            "solved_questions": solved_questions,
            "questions_left": questions_left,
            "progress_percentage": int(progress),
            "pod": pod_data,
            "sheets": sheet_data
        })