from django.urls import path, include
from . import problem_views, jovac_views, views, question_generator, batch_views, sheet_views, article_views, sheet_apis, achievers, flames_views, alumni_views

urlpatterns = [
    path("", views.index, name="administration"),
    
    path("view_student_profile/<int:id>", views.view_student_profile, name="administration_view_student_profile"),
    path("fetch_view_student_profile/<int:id>", views.fetch_view_student_profile, name="fetch_view_student_profile"),
    
    # ========================= DATA WORK ============================
    
    path("all_students/", views.all_students, name="all_students"),
    path("fetch_all_students/", views.fetch_all_students, name="fetch_all_students"),
    
    path('students/<int:student_id>/change-password/', views.change_password, name='administration_change_student_password'),


    path("all_instructors/", views.all_instructors, name="administrator_all_instructors"),
    path("add_instructor/", views.add_instructor, name="administrator_add_instructor"),
    
    path("feedbacks/", views.feedbacks, name="administrator_feedbacks"),
    
    # ========================= NOTIFICATIONS WORK ==========================
    
    path("notifications/", views.notifications, name="administrator_notifications"),
    path("delete_notification/<int:id>/", views.delete_notification, name="delete_notification"),
    path("edit_notification/<int:id>/", views.edit_notification, name="edit_notification"),
    
    # ========================= ANONYMOUS MESSAGES WORK ==========================
    
    path("messages/", views.administrator_anonymous_message, name="administrator_anonymous_message"),
    path("reply_message/<int:id>/", views.reply_message, name="reply_message"),
    path("edit_reply/<int:id>/", views.edit_reply, name="edit_reply"),
    
    # ========================= PROFILE WORK =========================
    
    path("administrator_profile/", views.administrator_profile, name="administrator_profile"),
    path("edit_administrator_profile/", views.edit_administrator_profile, name="edit_administrator_profile"),
    path('upload_administrator_profile', views.upload_administrator_profile, name='upload_administrator_profile'),
    path("change_administrator_password", views.change_administrator_password, name="change_administrator_password"),
    
    # ============================ PROBLMES WORK ==========================
    
    path("administrator_problems/", problem_views.administrator_problems, name="administrator_problems"),
    path("fetch_problems/", problem_views.fetch_problems, name="administrator_fetch_problems"),
    
    path("add_question/", problem_views.add_question, name="add_question"),
    path("delete_question/<int:id>", problem_views.delete_question, name="delete_question"),
    path("edit_question/<int:id>", problem_views.edit_question, name="edit_question"),
    
    path("test_cases/<slug:slug>/", problem_views.test_cases, name="test_cases"),
    path("add_test_case/<slug:slug>/", problem_views.add_test_case, name="add_test_case"),
    path("add_test_case_using_json/<slug:slug>/", problem_views.add_test_cases, name="add_test_cases_using_json_case"),    
    
    path("delete_test_case/<int:id>/", problem_views.delete_test_case, name="delete_test_case"),
    path("edit_test_case/<int:id>/", problem_views.edit_test_case, name="edit_test_case"),
    
    path("driver_code/<slug:slug>/", problem_views.driver_code, name="driver_code"),
    
    path("test_code/<slug:slug>/", problem_views.test_code, name="test_code"),
    path('submit_code/<slug:slug>/', problem_views.submit_code, name='administrator_submit_code'),

    
    path("question_requests/", problem_views.question_requests, name="question_requests"),
    path("approve_question/<int:id>/", problem_views.approve_question, name="approve_question"),
    path("reject_question/<int:id>/", problem_views.reject_question, name="reject_question"),
    
    # ================================= POD WORK ===========================
    
    path("administrator_pod", problem_views.administrator_pod, name="administrator_pod"),
    path("set_pod", problem_views.set_pod, name="set_pod"),
    
    path("save_pod/<int:id>/", problem_views.save_pod, name="save_pod"),
    
    path('generate-description/', question_generator.generate_description, name='generate_description'),
    
    # path('upload/image', views.upload_image, name='upload_image'),

    # Achievement Management URLs
    path('achievements/', achievers.achievements_view, name='achievements'),
    path('achievements/api/get', achievers.get_achievements, name='get_achievements'),
    path('achievements/api/create', achievers.create_achievement, name='create_achievement'),
    path('achievements/api/<int:achievement_id>', achievers.get_achievement, name='get_achievement'),
    path('achievements/api/<int:achievement_id>/update', achievers.update_achievement, name='update_achievement'),
    path('achievements/api/<int:achievement_id>/delete', achievers.delete_achievement, name='delete_achievement'),

]

# ========================= BATCH WORK ==========================

urlpatterns += [
    path("batches/", batch_views.batches, name="administrator_batches"),
    path("add_batch/", batch_views.add_batch, name="administrator_add_batch"),
    # path("delete_batch/<int:id>/", batch_views.delete_batch, name="delete_batch"),
    # path("edit_batch/<int:id>/",  batch_views.edit_batch, name="edit_batch"),
    
    path("enrollment_requests/", batch_views.enrollment_requests, name="administrator_enrollment_requests"),
    path("fetch_pending_enrollments/", batch_views.fetch_pending_enrollments, name="administrator_fetch_pending_enrollments"),
    path("fetch_rejected_enrollments/", batch_views.fetch_rejected_enrollments, name="administrator_fetch_rejected_enrollments"),
    
    path('approve-all/', batch_views.approve_all_enrollments, name='approve_all_enrollments'),
    path("approve_enrollment/<int:id>", batch_views.approve_enrollment, name="administrator_approve_enrollment"),
    path("reject_enrollment/<int:id>", batch_views.reject_enrollment, name="administrator_reject_enrollment"),
    
    path("batch/<slug:slug>/", batch_views.batch, name="administrator_batch"),
    
    path("administrator_set_pod_for_batch/<slug:slug>/", batch_views.administrator_set_pod_for_batch, name="administrator_pod_for_batch"),
    path('fetch-questions/', batch_views.fetch_questions, name='administrator_fetch_pod_questions_for_batch'),
    path('set-pod-ajax/<slug:slug>/', batch_views.set_pod, name='administrator_set_pod_for_batch'),


    
    path("view_submissions/<slug:slug>/", batch_views.view_submissions, name="administrator_view_submissions"),
    
    path("batch_leaderboard/<slug:slug>", batch_views.leaderboard, name="administrator_batch_leaderboard"),
    path("batch_leaderboard_api/<slug:slug>", batch_views.fetch_batch_leaderboard, name="administrator_fetch_batch_leaderboard"),
    
    # ============================ COURSE SPECIFIC ENROLLMENT WORK ===========
    
    path("course_enrollment_requests/<slug:slug>", batch_views.batch_enrollment_requests, name="administrator_batch_enrollment_requests"),
    path("fetch_pending_enrollments_of_batch/<slug:slug>", batch_views.fetch_pending_enrollments_of_batch, name="administrator_fetch_pending_enrollments_of_batch"),
    path("fetch_rejected_enrollments_of_batch/<slug:slug>", batch_views.fetch_rejected_enrollments_of_batch, name="administrator_fetch_rejected_enrollments_of_batch"),
    
    path('approve-all_batch/<int:id>', batch_views.approve_all_enrollments_batch, name='approve_all_enrollments_batch'),
    path("approve_enrollment_batch/<int:id>", batch_views.approve_enrollment_batch, name="administrator_approve_enrollment_batch"),
    path("reject_enrollment_batch/<int:id>", batch_views.reject_enrollment_batch, name="administrator_reject_enrollment_batch"),
   
]

# ========================= SHEET WORK ==========================

urlpatterns += [
    path("sheets/", sheet_views.sheets, name="administrator_sheets"),
    path("add_sheet/", sheet_views.add_sheet, name="administrator_add_sheet"),
    path("pending_sheet", sheet_views.administrator_pending_sheet, name="administrator_pending_sheet"),
    path("administrator_approve_sheet/<int:id>", sheet_views.administrator_approve_sheet, name="administrator_approve_sheet"),
    path("sheet/<slug:slug>/edit/", sheet_views.edit_sheet, name="administrator_edit_sheet"),
    path("delete_sheet/<int:id>/", sheet_views.delete_sheet, name="administrator_delete_sheet"),
    
    
    path("sheet/<slug:slug>/", sheet_views.sheet, name="administrator_sheet"),
    
    path("get_excluded_questions/<int:sheet_id>/", sheet_views.get_excluded_questions, name="get_excluded_questions"),
    
    path("remove_question_from_sheet/<int:sheet_id>/<int:question_id>/", sheet_views.remove_question_from_sheet, name="administrator_remove_from_sheet"),
    
    path("make_duplicate/<int:sheet_id>/<int:question_id>/", sheet_views.make_duplicate, name="administrator_make_duplicate"),
    path("add_new_question/<slug:slug>/", sheet_views.add_new_question, name="administrator_add_new_question"),
    
    path("add_question_json/<slug:slug>/", sheet_views.add_question_json, name="administrator_add_question_json"),
    path("reorder/<slug:slug>/", sheet_views.reorder, name="administrator_reorder"),
    
    path("sheet_leaderboard/<slug:slug>", sheet_views.leaderboard, name="administrator_leaderboard"),
    path("sheet_leaderboard_api/<slug:slug>", sheet_views.sheet_leaderboard, name="administrator_sheet_leaderboard"),
    
    path("reorder/<slug:slug>/", sheet_views.reorder, name="administrator_reorder"),
    path('update-sheet-order/<int:sheet_id>/', sheet_views.update_sheet_order, name='update_sheet_order'),

    path("administrator_set_sheet_timer/<int:sheet_id>/", sheet_views.set_sheet_timer, name="administrator_set_sheet_timer"),
    path("fetch_sheet_timer/<int:sheet_id>/", sheet_views.fetch_sheet_timer, name="fetch_sheet_timer"),
    
    path('download-leaderboard/<slug:slug>/', sheet_views.download_leaderboard_excel, name='download_leaderboard'),

    
    # ====================================== ENABLE / DISABLE SHEET ===================================
    
    path('sheet/<slug:slug>/toggle-status/', sheet_views.toggle_sheet_status, name='toggle_sheet_status'),

]

# ========================= ARTICLES WORK ==========================

urlpatterns += [
    path("articles/", article_views.articles, name="administrator_articles"),
    path("article/<slug:slug>/", article_views.article, name="administrator_article"),
    
    path("add_article/", article_views.add_article, name="administrator_add_article"),
    path("fetch_all_articles/", article_views.fetch_all_articles, name="administrator_fetch_all_articles"),
    
    path("delete_article/<int:id>/", article_views.delete_article, name="administrator_delete_article"),
    path("edit_article/<int:id>/", article_views.edit_article, name="administrator_edit_article"),
    
]

urlpatterns += [
    path("fetch_all_sheets/", sheet_apis.fetch_all_sheets, name="staff_fetch_all_sheets"),
    path('api/submissions/<slug:slug>/', sheet_apis.fetch_question_submissions, name='fetch_question_submissions'),

]

urlpatterns += [
    path('get-user-stats/', views.get_user_stats, name='get_user_stats'),

]

# Flames Management 
urlpatterns += [
    path("flames/courses/", flames_views.flames_courses, name="admin_flames_courses"),
    path("flames/registrations/", flames_views.flames_registrations, name="admin_flames_registrations"),
    
    path("flames/registrations/ajax/", flames_views.admin_registrations_ajax, name="admin_registrations_ajax"),
    
    path("flames/course/<int:course_id>/", flames_views.admin_course_detail, name="admin_course_detail"),
    path("flames/course/add/", flames_views.admin_add_course, name="admin_add_course"),
    path("flames/course/edit/<int:course_id>/", flames_views.admin_edit_course, name="admin_edit_course"),
    path("flames/toggle-course-status/", flames_views.admin_toggle_course_status, name="admin_toggle_course_status"),
    path("flames/registration-details/", flames_views.admin_registration_details, name="admin_registration_details"),
    path("flames/update-registration-status/", flames_views.admin_update_registration_status, name="admin_update_registration_status"),
    path("flames/update-registration-notes/", flames_views.admin_update_registration_notes, name="admin_update_registration_notes"),
    path("flames/delete-registration/", flames_views.admin_delete_registration, name="admin_delete_registration"),
    path("flames/add-testimonial/", flames_views.admin_add_testimonial, name="admin_add_testimonial"),
    
    # Email functionality
    path("flames/emails/", flames_views.admin_flames_emails, name="admin_flames_emails"),
    path("flames/emails/count-recipients/", flames_views.admin_count_flames_email_recipients, name="admin_count_flames_email_recipients"),
    path("flames/emails/send/", flames_views.admin_flames_emails, name="admin_send_flames_emails"),
    
    
    path("export-to-excel", flames_views.export_flames_registrations_to_excel, name="export_flames_registrations_to_excel"),
]


# Alumni Management
urlpatterns += [
    path('alumni/', alumni_views.alumni_management, name='alumni_management'),
    path('alumni/<int:alumni_id>/', alumni_views.alumni_details, name='alumni_details'),
    path('alumni/add/', alumni_views.add_alumni, name='add_alumni'),
    path('alumni/update/<int:alumni_id>/', alumni_views.update_alumni, name='update_alumni'),
    path('alumni/delete/<int:alumni_id>/', alumni_views.delete_alumni, name='delete_alumni'),
    path('alumni/generate-referral/<int:alumni_id>/', alumni_views.generate_referral_code, name='generate_referral_code'),
    path('alumni/toggle-referral-status/<int:code_id>/', alumni_views.toggle_referral_code_status, name='toggle_referral_code_status'),
    path('alumni/update-referral-code/<int:code_id>/', alumni_views.update_referral_code, name='update_referral_code'),
    path('alumni/stats/', alumni_views.alumni_stats, name='alumni_stats'),
    path('alumni/list-ajax/', alumni_views.alumni_list_ajax, name='alumni_list_ajax'),
]

# JOVAC Work

urlpatterns += [

    path("jovacs/", jovac_views.jovacs, name="administrator_jovacs"),
    path("jovac/<slug:slug>", jovac_views.jovac, name="administrator_jovac"),
    path("jovac/add_course/", jovac_views.add_course, name="administrator_add_jovac"),
    path("jovac/edit_course/<slug:slug>/", jovac_views.edit_course, name="administrator_edit_jovac"),

    path("add_assignment/<slug:slug>", jovac_views.add_assignment, name="administrator_add_assignment"),
    path("edit_assignment/<int:id>", jovac_views.edit_assignment, name="administrator_edit_assignment"),

    path("submissions/<int:id>/", jovac_views.view_submissions, name="view_assignment_submissions"),
    path("delete_assignment/<int:id>/", jovac_views.delete_assignment, name="administrator_delete_assignment"),

]