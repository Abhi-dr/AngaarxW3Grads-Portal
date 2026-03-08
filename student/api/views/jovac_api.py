"""
JOVAC API Views
Handles REST API endpoints for JOVAC course management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, CharField

from student.api.permissions import IsStudent
from student.models import Course, CourseRegistration
from student.api.serializers.batch_serializers import CourseListSerializer


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

        approved_courses = all_courses.filter(registration_status='Approved')
        pending_courses = all_courses.filter(registration_status='Pending')
        rejected_courses = all_courses.filter(registration_status='Rejected')
        
        other_courses = [
            c for c in all_courses 
            if c.registration_status not in ['Approved', 'Pending', 'Rejected']
        ]

        return Response({
            "success": True,
            "courses": {
                "approved_courses": CourseListSerializer(approved_courses, many=True).data,
                "pending_courses": CourseListSerializer(pending_courses, many=True).data,
                "rejected_courses": CourseListSerializer(rejected_courses, many=True).data,
                "other_courses": CourseListSerializer(other_courses, many=True).data,
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
