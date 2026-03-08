# API Package
# Re-export views from api/views package for backward compatibility
from .views import (
    ProfileAPIView,
    ChangePasswordAPIView,
    UploadProfilePictureAPIView,
    FeedbackAPIView,
    MyCertificatesAPIView,
    ViewCertificateAPIView,
)

__all__ = [
    'ProfileAPIView',
    'ChangePasswordAPIView',
    'UploadProfilePictureAPIView',
    'FeedbackAPIView',
    'MyCertificatesAPIView',
    'ViewCertificateAPIView',
]
