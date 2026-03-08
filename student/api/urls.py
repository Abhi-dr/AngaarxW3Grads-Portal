from django.urls import path
from student.api.views.dashboard_api import StudentProfileView, StudentDashboardView
from student.api.views.batch_api import BatchListView, BatchDetailView
from student.api.views.sheet_api import SheetDetailView, QuestionReadOnlyView
from student.api.views.jovac_api import JOVACListView, JOVACCourseDetailView, JOVACCourseSheetsView, JOVACSheetAssignmentsView

app_name = 'student_api'

urlpatterns = [
    path('profile/', StudentProfileView.as_view(), name='api_student_profile'),
    path('dashboard/', StudentDashboardView.as_view(), name='api_student_dashboard'),
    
    path('batches/', BatchListView.as_view(), name='api_student_batches'),
    path('batch/<slug:slug>/', BatchDetailView.as_view(), name='api_batch_detail'),
    
    path('jovac/courses/', JOVACListView.as_view(), name='api_jovac_courses'),
    path('jovac/courses/<slug:slug>/', JOVACCourseDetailView.as_view(), name='api_jovac_course_detail'),
    path('jovac/courses/<slug:slug>/sheets/', JOVACCourseSheetsView.as_view(), name='api_jovac_course_sheets'),
    path('jovac/courses/<slug:course_slug>/sheets/<slug:sheet_slug>/assignments/', JOVACSheetAssignmentsView.as_view(), name='api_jovac_sheet_assignments'),
    
    path('sheet/<slug:slug>/', SheetDetailView.as_view(), name='api_sheet_detail'),
    path('question/<slug:slug>/', QuestionReadOnlyView.as_view(), name='api_question_readonly'),
]
