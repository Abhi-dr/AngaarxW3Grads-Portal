from django.urls import path
from . import batch_views, views, doubt_solver

urlpatterns = [
    path("", views.dashboard, name="student"),
    
    # ========================= SESSION WORK =========================
    
    path("get_random_question/", views.get_random_question, name="get_random_question"),
    path('restore_streak/', views.restore_streak, name='restore_streak'),
    
    path("leveller", views.leveller, name="leveller"),
    
    # ======================== AI DOUBT SOLVER ========================
    
    path("AI-Doubt-Solver", doubt_solver.ask_doubt, name="doubt_solver"),
    
    # ========================= PROFILE WORK =========================
    path("my_profile/", views.my_profile, name="my_profile"),
    path("edit_profile/", views.edit_profile, name="edit_profile"),
    path('upload_profile', views.upload_profile, name='upload_profile'),
    path("change_password", views.change_password, name="change_password"),
    
    # ======================== HELP DESK WORK ========================
    
    path("notifications/", views.notifications, name="notifications"),
    path("anonymous_message/", views.anonymous_message, name="anonymous_message"),
    path("new_message", views.new_message, name="new_message"),
    path("feedback", views.feedback, name="feedback"),
    
]
 
# ========================================= BATCH WORK =========================================

urlpatterns += [
    path("my_courses/", batch_views.my_batches, name="my_batches"),
    path("enroll_course/<int:id>/", batch_views.enroll_batch, name="enroll_batch"),
    path("<slug:slug>/", batch_views.batch, name="batch"),
    path("sheet/<slug:slug>/", batch_views.my_sheet, name="my_sheet"),
    path("sheet_progress/<int:sheet_id>/", batch_views.sheet_progress, name="sheet_progress"),
    path("fetch_sheet_questions/<int:id>/", batch_views.fetch_sheet_questions, name="fetch_sheet_questions"),
    
    
]

