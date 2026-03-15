from django.urls import path, include
from rest_framework.routers import DefaultRouter
from administration.api.views.batch_api import BatchAdminViewSet
from administration.api.views.sheet_api import SheetAdminViewSet
from administration.api.views.jovac_api import (
    CourseToggleActiveView,
    CourseAdminViewSet,
    CourseSheetAdminViewSet,
    AssignmentAdminViewSet,
    TestCaseAdminViewSet,
    DriverCodeAdminViewSet,
)

router = DefaultRouter()
router.register(r'batches', BatchAdminViewSet, basename='admin-batch')
router.register(r'sheets', SheetAdminViewSet, basename='admin-sheet')
router.register(r'courses', CourseAdminViewSet, basename='admin-course')
router.register(r'course-sheets', CourseSheetAdminViewSet, basename='admin-course-sheet')
router.register(r'assignments', AssignmentAdminViewSet, basename='admin-assignment')
router.register(r'test-cases', TestCaseAdminViewSet, basename='admin-test-case')
router.register(r'driver-codes', DriverCodeAdminViewSet, basename='admin-driver-code')

urlpatterns = [
    path('', include(router.urls)),
    path('courses/<slug:slug>/toggle-active/', CourseToggleActiveView.as_view(), name='admin-course-toggle-active'),
]
