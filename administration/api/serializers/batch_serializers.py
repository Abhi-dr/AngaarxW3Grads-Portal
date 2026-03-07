from rest_framework import serializers
from practice.models import Batch

class BatchAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for Administrator to Create/Read/Update/Delete Batches.
    Handles the `required_fields` ListField natively and allows thumbnail uploads.
    """
    # required_fields is stored as a JSONField / CommaSeparatedCharField in some architectures.
    # Assuming practice.models.Batch has a JSONField or similar iterable field for required_fields.
    
    class Meta:
        model = Batch
        fields = ['id', 'name', 'slug', 'description', 'thumbnail', 'required_fields']
        read_only_fields = ['id', 'slug']
