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
        
        # JOVAC Course Data with registration status
        all_courses = Course.objects.annotate(
            registration_status=Case(
                When(courseregistration__student=student, courseregistration__status='Approved', then=Value('Approved')),
                When(courseregistration__student=student, courseregistration__status='Pending', then=Value('Pending')),
                When(courseregistration__student=student, courseregistration__status='Rejected', then=Value('Rejected')),
                default=Value('Not Enrolled'),
                output_field=CharField(),
            )
        ).prefetch_related('instructors').distinct()

        # My Courses: Only approved/enrolled courses
        my_courses = all_courses.filter(registration_status='Approved')
        
        # Available Courses: Only courses not enrolled/requested
        available_courses = all_courses.filter(registration_status='Not Enrolled')

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
        sheets = course.sheets.filter(is_active=True).order_by('order', 'id')
        
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
        
        # Get all course sheets for this course
        course_sheets = CourseSheet.objects.filter(course=course).order_by('id')
        
        return Response({
            "success": True,
            "sheets": CourseSheetSerializer(course_sheets, many=True).data,
            "course": {
                "name": course.name,
                "slug": course.slug,
                "instructor_names": course.get_instructor_names(),
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
        
        # Get ordered assignments
        assignments = course_sheet.get_ordered_assignments()
        
        # Get submitted assignment IDs for this student
        submitted_assignment_ids = AssignmentSubmission.objects.filter(
            student=student
        ).values_list('assignment_id', flat=True)
        
        # Add is_submitted flag to each assignment
        for assignment in assignments:
            assignment.is_submitted = assignment.id in submitted_assignment_ids
        
        # Get current time for deadline checks
        current_time = timezone.now()
        
        return Response({
            "success": True,
            "assignments": AssignmentListSerializer(assignments, many=True).data,
            "course": {
                "name": course.name,
                "slug": course.slug,
                "instructor_names": course.get_instructor_names(),
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

