from django.urls import path, include
from rest_framework.routers import DefaultRouter
from administration.api.views.batch_api import BatchAdminViewSet
from administration.api.views.sheet_api import SheetAdminViewSet

router = DefaultRouter()
router.register(r'batches', BatchAdminViewSet, basename='admin-batch')
router.register(r'sheets', SheetAdminViewSet, basename='admin-sheet')

urlpatterns = [
    path('', include(router.urls)),
]
