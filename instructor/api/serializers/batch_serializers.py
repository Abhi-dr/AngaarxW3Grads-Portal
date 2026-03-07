from rest_framework import serializers
from practice.models import Batch

class BatchInstructorSerializer(serializers.ModelSerializer):
    """
    Read-only Serializer for Instructors to list Batches.
    Instructors generally don't create or modify batches directly without admin review.
    """
    
    class Meta:
        model = Batch
        fields = ['id', 'name', 'slug', 'description', 'thumbnail', 'required_fields']
        read_only_fields = fields # All read-only
