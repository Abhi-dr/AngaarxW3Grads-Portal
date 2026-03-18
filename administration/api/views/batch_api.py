from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from practice.models import Batch
from administration.api.serializers.batch_serializers import BatchAdminSerializer
from administration.api.permissions import IsAdministratorOrInstructor, IsAdministrator

class BatchAdminViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Administrators to manage Batches.
    Supports GET, POST, PUT, PATCH, DELETE.
    Handles Multipart data for thumbnail image uploads.
    """
    queryset = Batch.objects.all().order_by('-id')
    serializer_class = BatchAdminSerializer
    permission_classes = [IsAdministratorOrInstructor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'

    def create(self, request, *args, **kwargs):
        # The serializer handles validation and saving, including the thumbnail
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='toggle-active', permission_classes=[IsAdministrator])
    def toggle_active(self, request, slug=None):
        """PATCH .../batches/<slug>/toggle-active/  — flip is_active"""
        batch = self.get_object()
        batch.is_active = not batch.is_active
        batch.save(update_fields=['is_active'])
        return Response({
            'success': True,
            'slug': batch.slug,
            'is_active': batch.is_active,
            'message': f'Course {"activated" if batch.is_active else "deactivated"} successfully.',
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='reorder-sheets', permission_classes=[IsAdministrator])
    def reorder_sheets(self, request, slug=None):
        """PATCH .../batches/<slug>/reorder-sheets/ — save custom sheet order.
        Body: {"order": [sheet_id, sheet_id, ...]}
        """
        batch = self.get_object()
        order = request.data.get('order', [])
        if not isinstance(order, list):
            return Response({'success': False, 'error': 'order must be a list of sheet IDs.'}, status=400)
        batch.sheet_order = {str(sheet_id): idx for idx, sheet_id in enumerate(order)}
        batch.save(update_fields=['sheet_order'])
        return Response({'success': True, 'message': 'Sheet order saved successfully.'})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({'success': True, 'data': serializer.data})
        
        print({'success': False, 'errors': serializer.errors})
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'success': True, 'message': 'Batch deleted successfully'}, status=status.HTTP_200_OK)

