from django.urls import path, include
from rest_framework.routers import DefaultRouter
from administration.api.views.batch_api import BatchAdminViewSet
from administration.api.views.sheet_api import SheetAdminViewSet
from administration.api.views.jovac_api import CourseToggleActiveView

router = DefaultRouter()
router.register(r'batches', BatchAdminViewSet, basename='admin-batch')
router.register(r'sheets', SheetAdminViewSet, basename='admin-sheet')

urlpatterns = [
    path('', include(router.urls)),
    path('courses/<slug:slug>/toggle-active/', CourseToggleActiveView.as_view(), name='admin-course-toggle-active'),
]
