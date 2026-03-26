from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from practice.models import Batch, Sheet
from instructor.api.serializers.batch_serializers import (
    BatchInstructorSerializer,
    BatchDetailInstructorSerializer,
    SheetDetailInstructorSerializer,
)
from instructor.api.permissions import IsInstructor

class BatchInstructorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-Only API for Instructors to list and retrieve Batches.
    """
    queryset = Batch.objects.all().order_by('-id')
    serializer_class = BatchInstructorSerializer
    permission_classes = [IsInstructor]
    lookup_field = 'slug'
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = BatchDetailInstructorSerializer(instance, context={'request': request})
        return Response({'success': True, 'data': serializer.data})

    @action(detail=True, methods=['patch'], url_path='reorder-sheets')
    def reorder_sheets(self, request, slug=None):
        """PATCH .../batches/<slug>/reorder-sheets/ — save custom sheet order for instructor."""
        batch = self.get_object()
        order = request.data.get('order', [])
        if not isinstance(order, list):
            return Response({'success': False, 'error': 'order must be a list of sheet IDs.'}, status=400)

        batch.sheet_order = {str(sheet_id): idx for idx, sheet_id in enumerate(order)}
        batch.save(update_fields=['sheet_order'])
        return Response({'success': True, 'message': 'Sheet order saved successfully.'})


class SheetInstructorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sheet.objects.all().order_by('-id')
    serializer_class = SheetDetailInstructorSerializer
    permission_classes = [IsInstructor]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        return Response({'success': True, 'data': serializer.data})

    @action(detail=False, methods=['get'], url_path='by-batch/(?P<batch_slug>[^/.]+)')
    def by_batch(self, request, batch_slug=None):
        batch = Batch.objects.filter(slug=batch_slug).first()
        if not batch:
            return Response({'success': False, 'error': 'Batch not found'}, status=404)
        sheets = batch.sheets.all().order_by('-id')
        data = [
            {
                'id': s.id,
                'name': s.name,
                'slug': s.slug,
                'thumbnail': s.thumbnail.url if s.thumbnail else None,
                'is_enabled': s.is_enabled,
                'sheet_type': s.sheet_type,
                'total_questions': s.get_total_questions(),
            }
            for s in sheets
        ]
        return Response({'success': True, 'data': data})
