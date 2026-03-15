from rest_framework import serializers
from student.event_models import Event, CertificateTemplate, Certificate
from accounts.models import CustomUser


class CertificateTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateTemplate
        fields = ['id', 'name', 'html_template', 'created_at']
        read_only_fields = ['id', 'created_at']


class EventSerializer(serializers.ModelSerializer):
    certificate_template_name = serializers.SerializerMethodField()
    certificate_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'code', 'start_date', 'end_date',
            'description', 'certificate_template', 'certificate_template_name',
            'certificate_count'
        ]
        read_only_fields = ['id']

    def get_certificate_template_name(self, obj):
        return obj.certificate_template.name if obj.certificate_template else None

    def get_certificate_count(self, obj):
        return obj.certificates.count()


class CertificateSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_email = serializers.SerializerMethodField()
    event_name = serializers.SerializerMethodField()
    event_code = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_id', 'event', 'event_name', 'event_code',
            'student', 'student_name', 'student_email',
            'issued_date', 'approved'
        ]
        read_only_fields = ['id', 'certificate_id']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip()

    def get_student_email(self, obj):
        return obj.student.email

    def get_event_name(self, obj):
        return obj.event.name

    def get_event_code(self, obj):
        return obj.event.code


class StudentSearchSerializer(serializers.ModelSerializer):
    """Light serializer for student search results."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
