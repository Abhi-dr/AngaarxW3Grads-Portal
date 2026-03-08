# Views Package
from .profile import (
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
