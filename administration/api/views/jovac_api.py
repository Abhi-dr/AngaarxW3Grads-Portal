from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.filters import SearchFilter
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
            if 'instructors' in request.data or str(request.data.get('instructors_present', '')).lower() in ['1', 'true', 'yes']:
                instructor_ids = request.data.getlist('instructors', [])
                instructor_ids = [i for i in instructor_ids if str(i).strip()]
                course.instructors.set(instructor_ids)
            return Response({'success': True, 'data': self.get_serializer(course).data})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'success': True, 'message': 'Course deleted successfully.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='sheets')
    def sheets(self, request, slug=None):
        """GET /api/v1/courses/<slug>/sheets/ — list sheets in custom order"""
        course = self.get_object()
        course_sheets = course.get_ordered_sheets()
        serializer = CourseSheetAdminSerializer(course_sheets, many=True, context={'request': request})
        return Response({'success': True, 'sheets': serializer.data})

    @action(detail=True, methods=['patch'], url_path='reorder-sheets')
    def reorder_sheets(self, request, slug=None):
        """PATCH /api/v1/courses/<slug>/reorder-sheets/ — save custom sheet order.
        Body: {"order": [sheet_id, sheet_id, ...]}
        """
        course = self.get_object()
        order = request.data.get('order', [])
        if not isinstance(order, list):
            return Response({'success': False, 'error': 'order must be a list of sheet IDs.'}, status=400)
        course.sheet_order = {str(sheet_id): idx for idx, sheet_id in enumerate(order)}
        course.save(update_fields=['sheet_order'])
        return Response({'success': True, 'message': 'Sheet order saved successfully.'})

    @action(detail=True, methods=['post'], url_path='bulk-update-sheets')
    def bulk_update_sheets(self, request, slug=None):
        """POST /api/v1/courses/<slug>/bulk-update-sheets/
        Body: {"action": "enable_all" | "approve_all"}
        """
        course = self.get_object()
        action_type = request.data.get('action')

        if action_type not in ['enable_all', 'approve_all']:
            return Response({'success': False, 'error': 'Invalid action. Use enable_all or approve_all.'}, status=400)

        sheets_qs = CourseSheet.objects.filter(course=course).distinct()

        if action_type == 'enable_all':
            updated_count = sheets_qs.exclude(is_enabled=True).update(is_enabled=True)
            return Response({
                'success': True,
                'updated_count': updated_count,
                'message': f'Enabled {updated_count} sheet(s) successfully.'
            })

        updated_count = sheets_qs.exclude(is_approved=True).update(is_approved=True)
        return Response({
            'success': True,
            'updated_count': updated_count,
            'message': f'Approved {updated_count} sheet(s) successfully.'
        })

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

    @action(detail=True, methods=['get'], url_path='items')
    def items(self, request, slug=None):
        """GET /api/v1/course-sheets/<slug>/items/ — list all mixed items (assignments, mcqs, coding)"""
        sheet = self.get_object()
        from administration.api.serializers.jovac_serializers import CourseSheetMixedItemSerializer
        items = sheet.get_ordered_items()
        serializer = CourseSheetMixedItemSerializer(items, many=True, context={'request': request})
        return Response({'success': True, 'items': serializer.data})
        
    @action(detail=True, methods=['patch'], url_path='reorder-items')
    def reorder_items(self, request, slug=None):
        """PATCH /api/v1/course-sheets/<slug>/reorder-items/ — save custom item order.
        Body: {"order": ["assignment_1", "mcq_5", "coding_9", ...]}
        """
        sheet = self.get_object()
        order = request.data.get('order', [])
        if not isinstance(order, list):
            return Response({'success': False, 'error': 'order must be a list of item IDs (e.g. assignment_1).'}, status=400)
        sheet.custom_order = {str(item_id): idx for idx, item_id in enumerate(order)}
        sheet.save(update_fields=['custom_order'])
        return Response({'success': True, 'message': 'Item order saved successfully.'})

    @action(detail=True, methods=['post'], url_path='link-item')
    def link_item(self, request, slug=None):
        """POST /api/v1/course-sheets/<slug>/link-item/
        Body: {"type": "MCQ" | "Coding", "item_id": 123}
        Links an existing question to this sheet. Assignments are linked in their own create endpoint.
        """
        sheet = self.get_object()
        item_type = request.data.get('type')
        item_id = request.data.get('item_id')
        
        if not item_type or not item_id:
            return Response({'success': False, 'error': 'type and item_id are required'}, status=400)
            
        if item_type == 'MCQ':
            from practice.models import MCQQuestion
            q = get_object_or_404(MCQQuestion, id=item_id)
            sheet.mcq_questions.add(q)
            return Response({'success': True, 'message': 'MCQ linked successfully'})
        elif item_type == 'Coding':
            from practice.models import Question
            q = get_object_or_404(Question, id=item_id)
            sheet.coding_questions.add(q)
            return Response({'success': True, 'message': 'Coding question linked successfully'})
        return Response({'success': False, 'error': 'Invalid type. Use MCQ or Coding.'}, status=400)

    @action(detail=True, methods=['post'], url_path='unlink-item')
    def unlink_item(self, request, slug=None):
        """POST /api/v1/course-sheets/<slug>/unlink-item/
        Body: {"type": "Assignment" | "MCQ" | "Coding", "item_id": 123}
        Unlinks an item from the sheet.
        """
        sheet = self.get_object()
        item_type = request.data.get('type')
        item_id = request.data.get('item_id')
        
        if not item_type or not item_id:
            return Response({'success': False, 'error': 'type and item_id are required'}, status=400)
            
        if item_type == 'Assignment':
            a = get_object_or_404(Assignment, id=item_id)
            a.course_sheets.remove(sheet)
        elif item_type == 'MCQ':
            from practice.models import MCQQuestion
            q = get_object_or_404(MCQQuestion, id=item_id)
            sheet.mcq_questions.remove(q)
        elif item_type == 'Coding':
            from practice.models import Question
            q = get_object_or_404(Question, id=item_id)
            sheet.coding_questions.remove(q)
        else:
            return Response({'success': False, 'error': 'Invalid type'}, status=400)
            
        # Clean up order dictionary
        full_key = f"{item_type.lower()}_{item_id}" if item_type != 'Assignment' else f"assignment_{item_id}"
        if full_key in sheet.custom_order:
            del sheet.custom_order[full_key]
            sheet.save(update_fields=['custom_order'])
            
        return Response({'success': True, 'message': 'Item unlinked successfully'})


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
# MCQQuestion CRUD ViewSet
# ============================================================

class MCQQuestionAdminViewSet(viewsets.ModelViewSet):
    """
    CRUD for MCQ Questions from within JOVAC module.
    """
    from practice.models import MCQQuestion
    queryset = MCQQuestion.objects.all().order_by('-created_at')
    from administration.api.serializers.jovac_serializers import MCQQuestionAdminSerializer
    serializer_class = MCQQuestionAdminSerializer
    permission_classes = [IsAdministratorOrInstructor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [SearchFilter]
    search_fields = ['question_text', 'slug', '=id']

    def create(self, request, *args, **kwargs):
        """
        Create MCQ for JOVAC. JOVAC MCQs are stored with a dummy 'sheet' 
        since they're linked via CourseSheet.mcq_questions M2M relationship.
        """
        from practice.models import Sheet
        
        # Get or create a default JOVAC sheet for storing JOVAC-created MCQs
        jovac_sheet, created = Sheet.objects.get_or_create(
            name='JOVAC MCQ Storage',
            slug='jovac-mcq-storage',
            defaults={
                'sheet_type': 'MCQ',
                'description': 'Placeholder sheet for JOVAC MCQ storage',
                'is_enabled': True,
                'is_approved': True,
            }
        )
        
        # If sheet already exists but is disabled, enable it
        if not created and (not jovac_sheet.is_enabled or not jovac_sheet.is_approved):
            jovac_sheet.is_enabled = True
            jovac_sheet.is_approved = True
            jovac_sheet.save()
        
        # Add the sheet to the request data for serialization
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['sheet'] = jovac_sheet.id
        
        # Create serializer with updated data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'id': serializer.instance.id
        }, status=status.HTTP_201_CREATED)


# ============================================================
# Question (Coding) CRUD ViewSet
# ============================================================

class QuestionAdminViewSet(viewsets.ModelViewSet):
    """
    CRUD for Coding Questions from within JOVAC module.
    """
    from practice.models import Question
    queryset = Question.objects.all().order_by('-id')
    from administration.api.serializers.jovac_serializers import QuestionAdminSerializer
    serializer_class = QuestionAdminSerializer
    permission_classes = [IsAdministratorOrInstructor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [SearchFilter]
    search_fields = ['title', 'description', 'slug', '=id']

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
