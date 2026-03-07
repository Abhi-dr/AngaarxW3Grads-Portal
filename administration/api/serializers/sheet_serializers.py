from rest_framework import serializers
from practice.models import Sheet, Batch

class SheetAdminSerializer(serializers.ModelSerializer):
    batches = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Batch.objects.all(),
        required=False
    )

    class Meta:
        model = Sheet
        fields = [
            'id', 'slug', 'name', 'description', 'thumbnail', 'batches', 
            'start_time', 'end_time', 'sheet_type', 'is_sequential', 
            'is_enabled', 'is_approved'
        ]
        read_only_fields = ['id', 'slug']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Enrich the batches with names and slugs for the UI to display easily
        representation['batches_info'] = [
            {'id': batch.id, 'slug': batch.slug, 'name': batch.name} 
            for batch in instance.batches.all()
        ]
        return representation
