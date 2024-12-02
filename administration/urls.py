from django.urls import path, include
from . import problem_views, views, question_generator, batch_views, sheet_views

urlpatterns = [
    path("", views.index, name="administration"),
    
    # ========================= DATA WORK ============================
    
    path("all_students/", views.all_students, name="all_students"),
    
    # ========================= NOTIFICATIONS WORK ==========================
    
    path("notifications/", views.notifications, name="instructor_notifications"),
    path("delete_notification/<int:id>/", views.delete_notification, name="delete_notification"),
    path("edit_notification/<int:id>/", views.edit_notification, name="edit_notification"),
    
    # ========================= ANONYMOUS MESSAGES WORK ==========================
    
    path("messages/", views.instructor_anonymous_message, name="instructor_anonymous_message"),
    path("reply_message/<int:id>/", views.reply_message, name="reply_message"),
    path("edit_reply/<int:id>/", views.edit_reply, name="edit_reply"),
    
    # ========================= PROFILE WORK =========================
    path("instructor_profile/", views.instructor_profile, name="instructor_profile"),
    path("edit_instructor_profile/", views.edit_instructor_profile, name="edit_instructor_profile"),
    path('upload_instructor_profile', views.upload_instructor_profile, name='upload_instructor_profile'),
    path("change_instructor_password", views.change_instructor_password, name="change_instructor_password"),
    
    # ============================ PROBLMES WORK ==========================
    
    path("instructor_problems/", problem_views.instructor_problems, name="instructor_problems"),
    path("fetch_problems/", problem_views.fetch_problems, name="instructor_fetch_problems"),
    
    path("add_question/", problem_views.add_question, name="add_question"),
    path("delete_question/<int:id>", problem_views.delete_question, name="delete_question"),
    path("edit_question/<int:id>", problem_views.edit_question, name="edit_question"),
    
    path("test_cases/<slug:slug>/", problem_views.test_cases, name="test_cases"),
    path("add_test_case/<slug:slug>/", problem_views.add_test_case, name="add_test_case"),
    path("delete_test_case/<int:id>/", problem_views.delete_test_case, name="delete_test_case"),
    path("edit_test_case/<int:id>/", problem_views.edit_test_case, name="edit_test_case"),
    
    path("driver_code/<slug:slug>/", problem_views.driver_code, name="driver_code"),
    
    path("test_code/<slug:slug>/", problem_views.test_code, name="test_code"),
    path('submit_code/<slug:slug>/', problem_views.submit_code, name='instructor_submit_code'),

    
    path("question_requests/", problem_views.question_requests, name="question_requests"),
    path("approve_question/<int:id>/", problem_views.approve_question, name="approve_question"),
    path("reject_question/<int:id>/", problem_views.reject_question, name="reject_question"),
    
    # ================================= POD WORK ===========================
    
    path("instructor_pod", problem_views.instructor_pod, name="instructor_pod"),
    path("set_pod", problem_views.set_pod, name="set_pod"),
    path("save_pod/<int:id>/", problem_views.save_pod, name="save_pod"),
    
    path('generate-description/', question_generator.generate_description, name='generate_description'),
    
]

# ========================= BATCH WORK ==========================

urlpatterns += [
    path("batches/", batch_views.batches, name="instructor_batches"),
    path("add_batch/", batch_views.add_batch, name="instructor_add_batch"),
    # path("delete_batch/<int:id>/", batch_views.delete_batch, name="delete_batch"),
    # path("edit_batch/<int:id>/",  batch_views.edit_batch, name="edit_batch"),
    
    path("enrollment_requests/", batch_views.enrollment_requests, name="instructor_enrollment_requests"),
    path("fetch_pending_enrollments/", batch_views.fetch_pending_enrollments, name="instructor_fetch_pending_enrollments"),
    path("fetch_rejected_enrollments/", batch_views.fetch_rejected_enrollments, name="instructor_fetch_rejected_enrollments"),
    
    path("approve_enrollment/<int:id>", batch_views.approve_enrollment, name="instructor_approve_enrollment"),
    path("reject_enrollment/<int:id>", batch_views.reject_enrollment, name="instructor_reject_enrollment"),
    
    path("batch/<slug:slug>/", batch_views.batch, name="instructor_batch"),
    path("instructor_set_pod_for_batch/<slug:slug>/", batch_views.instructor_set_pod_for_batch, name="instructor_set_pod_for_batch"),
    path("view_submissions/<slug:slug>/", batch_views.view_submissions, name="instructor_view_submissions"),
   
]

# ========================= SHEET WORK ==========================

urlpatterns += [
    path("sheets/", sheet_views.sheets, name="instructor_sheets"),
    path("add_sheet/", sheet_views.add_sheet, name="instructor_add_sheet"),
    path("delete_sheet/<int:id>/", sheet_views.delete_sheet, name="instructor_delete_sheet"),
    path("sheet/<slug:slug>/", sheet_views.sheet, name="instructor_sheet"),
    path("get_excluded_questions/<int:sheet_id>/", sheet_views.get_excluded_questions, name="get_excluded_questions"),
    
    path("add_question_to_sheet/<int:sheet_id>/<int:question_id>/", sheet_views.add_question_to_sheet, name="add_question_to_sheet"),
    path("remove_question_from_sheet/<int:sheet_id>/<int:question_id>/", sheet_views.remove_question_from_sheet, name="instructor_remove_from_sheet"),
]
