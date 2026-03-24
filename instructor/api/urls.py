from django.urls import path, include
from rest_framework.routers import DefaultRouter
from instructor.api.views.batch_api import BatchInstructorViewSet, SheetInstructorViewSet
from administration.api.views.jovac_api import (
    CourseAdminViewSet,
    CourseSheetAdminViewSet,
    AssignmentAdminViewSet,
    MCQQuestionAdminViewSet,
    QuestionAdminViewSet,
    TestCaseAdminViewSet,
    DriverCodeAdminViewSet,
)

router = DefaultRouter()
router.register(r'batches', BatchInstructorViewSet, basename='instructor-batch')
router.register(r'sheets', SheetInstructorViewSet, basename='instructor-sheet')
router.register(r'courses', CourseAdminViewSet, basename='instructor-course')
router.register(r'course-sheets', CourseSheetAdminViewSet, basename='instructor-course-sheet')
router.register(r'assignments', AssignmentAdminViewSet, basename='instructor-assignment')
router.register(r'mcq-questions', MCQQuestionAdminViewSet, basename='instructor-mcq-question')
router.register(r'coding-questions', QuestionAdminViewSet, basename='instructor-coding-question')
router.register(r'test-cases', TestCaseAdminViewSet, basename='instructor-test-case')
router.register(r'driver-codes', DriverCodeAdminViewSet, basename='instructor-driver-code')

urlpatterns = [
    path('', include(router.urls)),
]
