from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, CharField
from django.utils import timezone

from student.api.permissions import IsStudent
from student.models import Course, CourseRegistration, CourseSheet, AssignmentSubmission, Assignment
from student.api.serializers.batch_serializers import CourseListSerializer, CourseSheetSerializer
from student.api.serializers.assignment_serializers import AssignmentListSerializer, AssignmentDetailSerializer


class JOVACListView(APIView):
    """
    Returns lists of JOVAC courses organized by registration status.
    GET /dashboard/api/v1/jovac/courses/
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user
        
        # Get IDs of courses the student is enrolled in or has interacted with
        enrolled_course_ids = CourseRegistration.objects.filter(
            student=student, 
            status='Approved'
        ).values_list('course_id', flat=True)
        
        all_interacted_course_ids = CourseRegistration.objects.filter(
            student=student
        ).values_list('course_id', flat=True)

        my_courses = Course.objects.filter(id__in=enrolled_course_ids, is_active=True).prefetch_related('instructors').distinct()
        available_courses = Course.objects.exclude(id__in=all_interacted_course_ids).filter(is_active=True).prefetch_related('instructors').distinct()
        
        # Manually attach registration_status attributes so the Serializer method field reads them correctly
        for course in my_courses:
            course.registration_status = 'Approved'
            
        for course in available_courses:
            course.registration_status = 'Not Enrolled'

        return Response({
            "success": True,
            "courses": {
                "my_courses": CourseListSerializer(my_courses, many=True).data,
                "available_courses": CourseListSerializer(available_courses, many=True).data,
            }
        })


class JOVACCourseDetailView(APIView):
    """
    Returns detailed information about a single JOVAC course.
    GET /dashboard/api/v1/jovac/courses/<slug>/
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, slug):
        student = request.user
        course = get_object_or_404(Course, slug=slug)
        
        # Get registration status
        registration = CourseRegistration.objects.filter(
            student=student, 
            course=course
        ).first()
        
        registration_status = 'Not Enrolled'
        if registration:
            registration_status = registration.status
        
        # Get course sheets
        sheets = course.sheets.filter(is_enabled=True).order_by('order', 'id')
        
        course_data = CourseListSerializer(course).data
        course_data['registration_status'] = registration_status
        course_data['description'] = course.description if hasattr(course, 'description') else ''
        course_data['sheets_count'] = sheets.count()
        
        return Response({
            "success": True,
            "course": course_data,
            "registration_status": registration_status,
        })


class JOVACCourseSheetsView(APIView):
    """
    Returns all sheets for a specific JOVAC course.
    GET /dashboard/api/v1/jovac/courses/<slug>/sheets/
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug)

        # Respect custom sheet ordering set by administrators
        course_sheets = course.get_ordered_sheets_enabled()

        return Response({
            "success": True,
            "sheets": CourseSheetSerializer(course_sheets, many=True).data,
            "course": {
                "name": course.name,
                "slug": course.slug,
            }
        })


class JOVACSheetAssignmentsView(APIView):
    """
    Returns all assignments for a specific JOVAC course sheet.
    GET /dashboard/api/v1/jovac/courses/<course_slug>/sheets/<sheet_slug>/assignments/
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, course_slug, sheet_slug):
        student = request.user
        course = get_object_or_404(Course, slug=course_slug)
        course_sheet = get_object_or_404(CourseSheet, course=course, slug=sheet_slug)
        
        # Get ordered mixed items
        items = course_sheet.get_ordered_items()
        
        # Get submitted assignment IDs for this student
        submitted_assignment_ids = AssignmentSubmission.objects.filter(
            student=student
        ).values_list('assignment_id', flat=True)
        
        from student.api.serializers.assignment_serializers import AssignmentListSerializer
        
        serialized_items = []
        for item in items:
            obj = item['obj']
            if item['type'] == 'Assignment':
                # Add is_submitted flag
                obj.is_submitted = obj.id in submitted_assignment_ids
                data = AssignmentListSerializer(obj).data
            elif item['type'] == 'MCQ':
                data = {
                    'id': obj.id,
                    'title': obj.question_text[:100] + ('...' if len(obj.question_text) > 100 else ''),
                    'slug': obj.slug,
                    'difficulty_level': obj.difficulty_level,
                    'is_tutorial': False,
                    'is_submitted': False, # Update this later if MCQ submissions are tracked here
                    'assignment_type': 'MCQ Question'
                }
            elif item['type'] == 'Coding':
                data = {
                    'id': obj.id,
                    'title': obj.title,
                    'slug': obj.slug,
                    'difficulty_level': obj.difficulty_level,
                    'is_tutorial': False,
                    'is_submitted': False, # Update this later if Coding submissions are tracked here
                    'assignment_type': 'Coding Question'
                }
            
            serialized_items.append({
                'item_id': item['item_id'],
                'type': item['type'],
                'pk': item['pk'],
                'data': data
            })
        
        # Get current time for deadline checks
        current_time = timezone.now()
        
        return Response({
            "success": True,
            "items": serialized_items,
            "course": {
                "name": course.name,
                "slug": course.slug,
            },
            "sheet": {
                "name": course_sheet.name,
                "slug": course_sheet.slug,
            },
            "current_time": current_time.isoformat(),
        })


class JOVACTutorialDetailView(APIView):
    """
    Returns detailed information about a specific JOVAC tutorial/assignment.
    GET /dashboard/api/v1/jovac/tutorial/<int:id>/
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, id):
        student = request.user
        
        # Get the tutorial by ID
        tutorial = get_object_or_404(Assignment, id=id)
        course = tutorial.course
        
        # Check if the user is enrolled in the course
        if not CourseRegistration.objects.filter(student=student, course=course).exists():
            return Response({
                "success": False,
                "error": "You are not enrolled in this course",
                "code": "NOT_ENROLLED"
            }, status=403)
        
        # Serialize the tutorial data
        tutorial_data = AssignmentDetailSerializer(tutorial).data
        
        return Response({
            "success": True,
            "tutorial": tutorial_data,
        })

