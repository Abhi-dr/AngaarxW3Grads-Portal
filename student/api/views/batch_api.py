from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, CharField

from student.api.permissions import IsStudent
from practice.models import Batch, EnrollmentRequest, Sheet
from student.models import Course, Notification
from student.api.serializers.batch_serializers import BatchListSerializer, CourseListSerializer
from student.api.serializers.sheet_serializers import SheetListSerializer

class BatchListView(APIView):
    """
    Returns lists of batches organized by enrollment status.
    Mimics the old fetch_my_batch_data JSON response.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        
        # Batch Data
        all_batches = Batch.objects.annotate(
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

        # jovac Data
        all_courses = Course.objects.annotate(
            registration_status=Case(
                When(courseregistration__student=student, courseregistration__status='Approved', then=Value('Approved')),
                When(courseregistration__student=student, courseregistration__status='Pending', then=Value('Pending')),
                When(courseregistration__student=student, courseregistration__status='Rejected', then=Value('Rejected')),
                default=Value('Not Enrolled'),
                output_field=CharField(),
            )
        ).prefetch_related('instructors').distinct()

        approved_courses = all_courses.filter(registration_status='Approved')
        pending_courses = all_courses.filter(registration_status='Pending')
        rejected_courses = all_courses.filter(registration_status='Rejected')
        
        other_courses = [
            c for c in all_courses 
            if c.registration_status not in ['Approved', 'Pending', 'Rejected']
        ]
        

        return Response({
            "success": True,
            "batches": {
                "student_batches": BatchListSerializer(student_batches, many=True).data,
                "pending_batches": BatchListSerializer(pending_batches, many=True).data,
                "rejected_batches": BatchListSerializer(rejected_batches, many=True).data,
                "other_batches": BatchListSerializer(other_batches, many=True).data,
            },
            "courses": {
                "approved_courses": CourseListSerializer(approved_courses, many=True).data,
                "pending_courses": CourseListSerializer(pending_courses, many=True).data,
                "rejected_courses": CourseListSerializer(rejected_courses, many=True).data,
                "other_courses": CourseListSerializer(other_courses, many=True).data,
            }
        })


class BatchDetailView(APIView):
    """
    Returns detailed information about a single batch, including its sheets and progress.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, slug):
        student = request.user
        batch = get_object_or_404(Batch, slug=slug)
        
        # Security: check if enrolled
        if not EnrollmentRequest.objects.filter(student=student, batch=batch, status='Accepted').exists():
            return Response({"error": "Not enrolled in this batch."}, status=403)
            
        sheets = Sheet.objects.filter(batches=batch, is_approved=True).order_by('id')
        
        # Calculate raw progress
        total_questions = 0
        solved_questions = 0
        for sheet in sheets:
            total_questions += sheet.get_total_questions()
            solved_questions += sheet.get_solved_questions(student)
            
        progress = (solved_questions / total_questions * 100) if total_questions > 0 else 0
        questions_left = total_questions - solved_questions
        
        sheet_data = SheetListSerializer(sheets, many=True).data
        
        # POD Data
        from practice.models import POD, Submission, MCQSubmission
        from datetime import datetime
        from student.api.serializers.sheet_serializers import PODSerializer
        
        pod_data = None
        pod = POD.objects.filter(batch=batch, date=datetime.now().date()).first()
        if pod:
            pod_serializer = PODSerializer(pod).data
            # Check if solved
            is_solved = Submission.objects.filter(user=student, question_id=pod.question.id, status='Accepted').exists()
            if not is_solved:
                is_solved = MCQSubmission.objects.filter(student=student, question_id=pod.question.id, is_correct=True).exists()
                
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
