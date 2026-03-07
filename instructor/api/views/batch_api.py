from rest_framework import viewsets
from rest_framework.response import Response

from practice.models import Batch
from instructor.api.serializers.batch_serializers import BatchInstructorSerializer
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
