"""
student/serializers.py
DRF serializers for the Student Profile API and Feedback API.
"""

from rest_framework import serializers
from accounts.models import CustomUser


# ─────────────────────────────────────────────────────────────────
# 1. Profile Serializer — GET / PATCH
# ─────────────────────────────────────────────────────────────────

class ProfileSerializer(serializers.ModelSerializer):
    """
    Read / partial-update serializer for CustomUser profile fields.
    profile_score and profile_pic_url are read-only computed fields.
    """

    profile_score = serializers.SerializerMethodField(read_only=True)
    profile_pic_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "gender",
            "college",
            "mobile_number",
            "dob",
            "linkedin_id",
            "github_id",
            "coins",
            "profile_pic_url",
            "profile_score",
        ]
        # coins are system-managed; other profile fields can be edited via PATCH
        read_only_fields = ["id", "coins", "profile_score", "profile_pic_url"]

    # ── Computed fields ──────────────────────────────────────────
    def get_profile_score(self, obj):
        return obj.get_profile_score()

    def get_profile_pic_url(self, obj):
        request = self.context.get("request")
        if obj.profile_pic and hasattr(obj.profile_pic, "url"):
            return request.build_absolute_uri(obj.profile_pic.url) if request else obj.profile_pic.url
        return None

    # ── Validation ───────────────────────────────────────────────
    def validate_mobile_number(self, value):
        if value and (not value.isdigit() or len(value) != 10):
            raise serializers.ValidationError("Mobile number must be exactly 10 digits.")
        return value

    # ── Save with coin rewards ───────────────────────────────────
    def update(self, instance, validated_data):
        coins_earned = 0

        field_coin_map = {
            "first_name": 5,
            "last_name": 5,
            "college": 5,
            "mobile_number": 10,
            "dob": 10,
            "linkedin_id": 20,
            "github_id": 20,
        }

        for field, bonus in field_coin_map.items():
            old_value = getattr(instance, field, None)
            new_value = validated_data.get(field)
            # Award coins only when filling a previously empty field
            if new_value and not old_value:
                coins_earned += bonus

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if coins_earned > 0:
            instance.coins += coins_earned

        instance.save()
        return instance


# ─────────────────────────────────────────────────────────────────
# 2. Change Password Serializer
# ─────────────────────────────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    old_password     = serializers.CharField(write_only=True)
    new_password     = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "New password and confirm password do not match."}
            )
        if data["old_password"] == data["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from old password."}
            )
        return data

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


# ─────────────────────────────────────────────────────────────────
# 3. Delete Account Serializer
# ─────────────────────────────────────────────────────────────────

class DeleteAccountSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, value):
        user = self.context["request"].user
        if value.strip() != user.username:
            raise serializers.ValidationError(
                "Username does not match. Account not deleted."
            )
        return value


# ─────────────────────────────────────────────────────────────────
# 4. Feedback Serializer
# ─────────────────────────────────────────────────────────────────

class FeedbackSerializer(serializers.Serializer):
    """
    Validates and creates a Feedback record for the authenticated student.
    """
    subject = serializers.CharField(max_length=255)
    message = serializers.CharField()

    def create(self, validated_data):
        from student.models import Feedback
        return Feedback.objects.create(
            student=self.context["request"].user,
            **validated_data,
        )


# ─────────────────────────────────────────────────────────────────
# 5. Certificate Serializer
# ─────────────────────────────────────────────────────────────────

class CertificateSerializer(serializers.Serializer):
    """
    Read-only serializer for Certificate records.
    Returns certificate details with related event information.
    """
    id = serializers.IntegerField(read_only=True)
    certificate_id = serializers.CharField(read_only=True)
    issued_date = serializers.DateField(read_only=True)
    approved = serializers.BooleanField(read_only=True)
    
    # Event nested data
    event_name = serializers.CharField(source='event.name', read_only=True)
    event_code = serializers.CharField(source='event.code', read_only=True)
    
    # Certificate view URL
    view_url = serializers.SerializerMethodField(read_only=True)
    
    def get_view_url(self, obj):
        from django.urls import reverse
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(
                reverse('student_view_certificate', kwargs={'id': obj.id})
            )
        return reverse('student_view_certificate', kwargs={'id': obj.id})
