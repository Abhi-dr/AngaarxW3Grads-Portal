from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from student.models import Course
from administration.api.permissions import IsAdministrator


class CourseToggleActiveView(APIView):
    """
    PATCH /administration/api/v1/courses/<slug>/toggle-active/
    Toggles the is_active flag on a JOVAC Course.
    Only accessible by administrators.
    """
    permission_classes = [IsAdministrator]

    def patch(self, request, slug):
        course = get_object_or_404(Course, slug=slug)
        course.is_active = not course.is_active
        course.save(update_fields=['is_active'])
        return Response({
            'success': True,
            'slug': course.slug,
            'is_active': course.is_active,
            'message': f'Course {"activated" if course.is_active else "deactivated"} successfully.',
        }, status=status.HTTP_200_OK)
