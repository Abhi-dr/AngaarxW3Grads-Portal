from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

from student.models import Course, CourseSheet, Assignment
from practice.models import Question, TestCase, DriverCode
from accounts.models import CustomUser

from administration.api.permissions import IsAdministratorOrInstructor, IsAdministrator
from administration.api.serializers.jovac_serializers import (
    CourseAdminSerializer, CourseSheetAdminSerializer,
    AssignmentAdminSerializer, TestCaseAdminSerializer, DriverCodeAdminSerializer
)


# ============================================================
# Course Toggle Active (existing, kept intact)
# ============================================================

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


# ============================================================
# Course CRUD ViewSet
# ============================================================

class CourseAdminViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for JOVAC Courses.
    GET    /api/v1/courses/             - list all
    POST   /api/v1/courses/             - create
    GET    /api/v1/courses/<slug>/      - retrieve
    PUT    /api/v1/courses/<slug>/      - update
    PATCH  /api/v1/courses/<slug>/      - partial update
    DELETE /api/v1/courses/<slug>/      - delete
    GET    /api/v1/courses/<slug>/sheets/  - list sheets of a course
    """
    queryset = Course.objects.all().prefetch_related('instructors').order_by('-created_at')
    serializer_class = CourseAdminSerializer
    permission_classes = [IsAdministratorOrInstructor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            course = serializer.save()
            # handle instructors
            instructor_ids = request.data.getlist('instructors', [])
            if instructor_ids:
                course.instructors.set(instructor_ids)
            return Response({'success': True, 'data': self.get_serializer(course).data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            course = serializer.save()
            # handle instructors update
            if 'instructors' in request.data:
                instructor_ids = request.data.getlist('instructors', [])
                course.instructors.set(instructor_ids)
            return Response({'success': True, 'data': self.get_serializer(course).data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'success': True, 'message': 'Course deleted successfully.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='sheets')
    def sheets(self, request, slug=None):
        """GET /api/v1/courses/<slug>/sheets/ — list all sheets for a course"""
        course = self.get_object()
        course_sheets = CourseSheet.objects.filter(course=course).order_by('id')
        serializer = CourseSheetAdminSerializer(course_sheets, many=True, context={'request': request})
        return Response({'success': True, 'sheets': serializer.data})

    @action(detail=True, methods=['get'], url_path='instructors')
    def instructors(self, request, slug=None):
        """GET /api/v1/courses/<slug>/instructors/ — list available instructors"""
        all_instructors = CustomUser.objects.filter(role='instructor').values('id', 'first_name', 'last_name', 'email')
        course = self.get_object()
        assigned_ids = list(course.instructors.values_list('id', flat=True))
        return Response({'success': True, 'instructors': list(all_instructors), 'assigned': assigned_ids})


# ============================================================
# CourseSheet CRUD ViewSet
# ============================================================

class CourseSheetAdminViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for JOVAC CourseSheets.
    GET    /api/v1/course-sheets/            - list all
    POST   /api/v1/course-sheets/            - create (requires course_slug in body)
    GET    /api/v1/course-sheets/<slug>/     - retrieve
    PUT    /api/v1/course-sheets/<slug>/     - update
    DELETE /api/v1/course-sheets/<slug>/     - delete
    """
    queryset = CourseSheet.objects.all().order_by('id')
    serializer_class = CourseSheetAdminSerializer
    permission_classes = [IsAdministratorOrInstructor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            sheet = serializer.save(created_by=request.user)
            # Attach to course
            course_slug = request.data.get('course_slug')
            if course_slug:
                course = get_object_or_404(Course, slug=course_slug)
                sheet.course.add(course)
            return Response({'success': True, 'data': self.get_serializer(sheet).data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({'success': True, 'data': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'success': True, 'message': 'Sheet deleted successfully.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='assignments')
    def assignments(self, request, slug=None):
        """GET /api/v1/course-sheets/<slug>/assignments/ — list all assignments for a sheet"""
        sheet = self.get_object()
        assignments = sheet.get_ordered_assignments()
        serializer = AssignmentAdminSerializer(assignments, many=True, context={'request': request})
        return Response({'success': True, 'assignments': serializer.data})


# ============================================================
# Assignment CRUD ViewSet
# ============================================================

class AssignmentAdminViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for JOVAC Assignments.
    POST   /api/v1/assignments/          - create (requires course_slug + sheet_slug in body)
    GET    /api/v1/assignments/<id>/     - retrieve
    PATCH  /api/v1/assignments/<id>/     - partial update
    DELETE /api/v1/assignments/<id>/     - delete
    """
    queryset = Assignment.objects.all().order_by('-created_at')
    serializer_class = AssignmentAdminSerializer
    permission_classes = [IsAdministratorOrInstructor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        course_slug = request.data.get('course_slug')
        sheet_slug = request.data.get('sheet_slug')

        if not course_slug or not sheet_slug:
            return Response({'success': False, 'error': 'course_slug and sheet_slug are required.'}, status=400)

        course = get_object_or_404(Course, slug=course_slug)
        sheet = get_object_or_404(CourseSheet, slug=sheet_slug, course=course)
        course_ct = ContentType.objects.get_for_model(course)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            assignment = serializer.save(
                content_type=course_ct,
                object_id=course.id,
            )
            assignment.course_sheets.add(sheet)
            return Response({'success': True, 'data': self.get_serializer(assignment).data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({'success': True, 'data': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'success': True, 'message': 'Assignment deleted successfully.'}, status=status.HTTP_200_OK)


# ============================================================
# TestCase CRUD ViewSet
# ============================================================

class TestCaseAdminViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for TestCases scoped to a Question.
    GET    /api/v1/test-cases/?question_slug=<slug>   - list test cases
    POST   /api/v1/test-cases/                        - create (requires question_slug)
    PATCH  /api/v1/test-cases/<id>/                   - update
    DELETE /api/v1/test-cases/<id>/                   - delete
    """
    serializer_class = TestCaseAdminSerializer
    permission_classes = [IsAdministratorOrInstructor]

    def get_queryset(self):
        question_slug = self.request.query_params.get('question_slug')
        if question_slug:
            question = get_object_or_404(Question, slug=question_slug)
            return TestCase.objects.filter(question=question).order_by('id')
        return TestCase.objects.all().order_by('id')

    def create(self, request, *args, **kwargs):
        question_slug = request.data.get('question_slug')
        if not question_slug:
            return Response({'success': False, 'error': 'question_slug is required.'}, status=400)
        question = get_object_or_404(Question, slug=question_slug)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(question=question)
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({'success': True, 'data': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'success': True, 'message': 'Test case deleted successfully.'}, status=status.HTTP_200_OK)


# ============================================================
# DriverCode CRUD ViewSet
# ============================================================

class DriverCodeAdminViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for DriverCodes scoped to a Question.
    GET    /api/v1/driver-codes/?question_slug=<slug>  - list driver codes
    POST   /api/v1/driver-codes/                       - create or upsert
    PATCH  /api/v1/driver-codes/<id>/                  - update
    """
    serializer_class = DriverCodeAdminSerializer
    permission_classes = [IsAdministratorOrInstructor]

    def get_queryset(self):
        question_slug = self.request.query_params.get('question_slug')
        if question_slug:
            question = get_object_or_404(Question, slug=question_slug)
            return DriverCode.objects.filter(question=question).order_by('language_id')
        return DriverCode.objects.all().order_by('language_id')

    def create(self, request, *args, **kwargs):
        question_slug = request.data.get('question_slug')
        if not question_slug:
            return Response({'success': False, 'error': 'question_slug is required.'}, status=400)
        question = get_object_or_404(Question, slug=question_slug)
        language_id = request.data.get('language_id')

        # Upsert: if a driver code exists for this language, update it
        existing = DriverCode.objects.filter(question=question, language_id=language_id).first()
        if existing:
            serializer = self.get_serializer(existing, data=request.data, partial=True)
            if serializer.is_valid():
                self.perform_update(serializer)
                return Response({'success': True, 'updated': True, 'data': serializer.data})
            return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(question=question)
            return Response({'success': True, 'updated': False, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({'success': True, 'data': serializer.data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
