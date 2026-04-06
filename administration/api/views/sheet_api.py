from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.filters import SearchFilter

from practice.models import Sheet
from administration.api.serializers.sheet_serializers import SheetAdminSerializer
from administration.api.permissions import IsAdministratorOrInstructor

class SheetAdminViewSet(viewsets.ModelViewSet):
    """
    Unified API for Administrators and Instructors to manage Sheets.
    Supports ?search= for name/description/type and ?page= for pagination.
    """
    queryset = Sheet.objects.all().order_by('-id')
    serializer_class = SheetAdminSerializer
    permission_classes = [IsAdministratorOrInstructor]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'slug'
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description', 'sheet_type']

    def perform_create(self, serializer):
        # Automatically set the currently logged in user as the creator
        serializer.save(created_by=self.request.user)
