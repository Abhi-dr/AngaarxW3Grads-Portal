import json
from rest_framework import serializers
from practice.models import Batch

class BatchAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for Administrator to Create/Read/Update/Delete Batches.
    Handles the `required_fields` ListField natively and allows thumbnail uploads.
    """

    class Meta:
        model = Batch
        fields = ['id', 'name', 'slug', 'description', 'thumbnail', 'required_fields', 'is_active']
        read_only_fields = ['id', 'slug']

    def to_internal_value(self, data):
        """
        When sent via multipart/form-data, required_fields may arrive as:
          - A JSON string: '["GitHub","LinkedIn"]'   -> parse it
          - A plain list already (API JSON body)     -> use as-is
          - Multiple separate string values (legacy) -> already a list
        """
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        rf = data.get('required_fields')
        if rf is not None:
            if isinstance(rf, str):
                try:
                    parsed = json.loads(rf)
                    data['required_fields'] = [v for v in parsed if v] if isinstance(parsed, list) else rf
                except (ValueError, TypeError):
                    # Fallback: treat as a single-item list or ignore empties
                    data['required_fields'] = [rf] if rf else []
            elif isinstance(rf, list):
                data['required_fields'] = [v for v in rf if v]
        return super().to_internal_value(data)

