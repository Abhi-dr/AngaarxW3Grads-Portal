from django.urls import path, include
from rest_framework.routers import DefaultRouter
from instructor.api.views.batch_api import BatchInstructorViewSet

router = DefaultRouter()
router.register(r'batches', BatchInstructorViewSet, basename='instructor-batch')

urlpatterns = [
    path('', include(router.urls)),
]
