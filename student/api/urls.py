from django.urls import path
from student.api.views.dashboard_api import StudentProfileView, StudentDashboardView
from student.api.views.batch_api import BatchListView, BatchDetailView
from student.api.views.sheet_api import SheetDetailView, QuestionReadOnlyView

app_name = 'student_api'

urlpatterns = [
    path('profile/', StudentProfileView.as_view(), name='api_student_profile'),
    path('dashboard/', StudentDashboardView.as_view(), name='api_student_dashboard'),
    
    path('batches/', BatchListView.as_view(), name='api_student_batches'),
    path('batch/<slug:slug>/', BatchDetailView.as_view(), name='api_batch_detail'),
    
    path('sheet/<slug:slug>/', SheetDetailView.as_view(), name='api_sheet_detail'),
    path('question/<slug:slug>/', QuestionReadOnlyView.as_view(), name='api_question_readonly'),
]
