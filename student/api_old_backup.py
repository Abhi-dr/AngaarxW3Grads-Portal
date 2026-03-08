"""
student/api.py
DRF APIView classes for the Student Profile REST API and Feedback API.

Endpoints under /dashboard/:
  Profile API  (/api/profile/)
    GET    /              — Retrieve profile
    PATCH  /              — Edit profile fields
    DELETE /              — Delete account (requires username confirmation)

    POST   /change-password/   — Change password
    POST   /upload-picture/    — Upload profile picture (multipart)

  Feedback API
    POST   /api/feedback/      — Submit feedback
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import logout as django_logout

from .serializers import (
    ProfileSerializer,
    ChangePasswordSerializer,
    DeleteAccountSerializer,
    FeedbackSerializer,
)


# ═══════════════════════════════════════════════════════════════════
# Profile View  — GET / PATCH / DELETE
# ═══════════════════════════════════════════════════════════════════

class ProfileAPIView(APIView):
    """
    Manages the authenticated student's profile.

    GET    → returns full profile JSON
    PATCH  → partial update of profile fields (awards coins for new data)
    DELETE → deletes account after username confirmation
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    # ── GET /dashboard/api/profile/ ──────────────────────────────
    def get(self, request):
        serializer = ProfileSerializer(
            request.user,
            context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ── PATCH /dashboard/api/profile/ ───────────────────────────
    def patch(self, request):
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,               # allow subset of fields
            context={"request": request}
        )
        if serializer.is_valid():
            updated_user = serializer.save()
            # Check how many coins were earned (compare before/after)
            coins_earned = updated_user.coins - request.user.coins
            response_data = serializer.data
            response_data["coins_earned"] = max(coins_earned, 0)
            if coins_earned > 0:
                response_data["message"] = (
                    f"Profile updated! You earned {coins_earned} sparks ✨"
                )
            else:
                response_data["message"] = "Profile updated successfully."
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ── DELETE /dashboard/api/profile/ ──────────────────────────
    def delete(self, request):
        serializer = DeleteAccountSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            django_logout(request)      # clear session before deleting user
            user.delete()
            return Response(
                {"message": "Account deleted successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════════
# Change Password View  — POST
# ═══════════════════════════════════════════════════════════════════

class ChangePasswordAPIView(APIView):
    """
    POST /dashboard/api/profile/change-password/

    Body: { old_password, new_password, confirm_password }
    On success: session remains valid (update_session_auth_hash is called).
    The frontend can redirect to login if desired.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.is_changed_password = True
            user.save()

            # Keep the user logged in after password change
            update_session_auth_hash(request, user)

            return Response(
                {"message": "Password changed successfully."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════════
# Upload Profile Picture View  — POST
# ═══════════════════════════════════════════════════════════════════

class UploadProfilePictureAPIView(APIView):
    """
    POST /dashboard/api/profile/upload-picture/

    Accepts multipart/form-data with field: profile_pic (image file).
    Max size: 5 MB.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    MAX_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB

    def post(self, request):
        file = request.FILES.get("profile_pic")

        if not file:
            return Response(
                {"error": "No file provided. Send a file with field name 'profile_pic'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if file.size > self.MAX_SIZE_BYTES:
            return Response(
                {"error": "Profile picture must be smaller than 5 MB."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        user.profile_pic = file
        user.save()

        pic_url = (
            request.build_absolute_uri(user.profile_pic.url)
            if user.profile_pic else None
        )

        return Response(
            {
                "message": "Profile picture updated successfully.",
                "profile_pic": pic_url,
            },
            status=status.HTTP_200_OK
        )


# ═══════════════════════════════════════════════════════════════════
# Feedback View  — POST
# ═══════════════════════════════════════════════════════════════════

class FeedbackAPIView(APIView):
    """
    POST /dashboard/api/feedback/

    Body (JSON): { "subject": "...", "message": "..." }
    Creates a Feedback record tied to the authenticated student.
    Returns: { "message": "Feedback submitted! Thank you 🙏" }
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        serializer = FeedbackSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Feedback submitted! Thank you 🙏"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════════
# My Certificates View  — GET
# ═══════════════════════════════════════════════════════════════════

class MyCertificatesAPIView(APIView):
    """
    GET /dashboard/api/certificates/
    
    Returns list of all certificates for the authenticated student.
    Includes event details and certificate view URL.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from student.event_models import Certificate
        from .serializers import CertificateSerializer
        
        certificates = Certificate.objects.filter(
            student=request.user
        ).select_related('event').order_by('-issued_date')
        
        serializer = CertificateSerializer(
            certificates,
            many=True,
            context={"request": request}
        )
        
        return Response(
            {
                "count": certificates.count(),
                "certificates": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = FeedbackSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Feedback submitted! Thank you 🙏"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
