from django.urls import path, include
from . import batch_views, views, doubt_solver, hackathon_views, flames_views, course_views, jovac_views

urlpatterns = [
    path("", views.dashboard, name="student"),
    
    # ========================= SESSION WORK =========================
    
    path("get_random_question/", views.get_random_question, name="get_random_question"),
    path('restore_streak/', views.restore_streak, name='restore_streak'),
    
    path("leveller", views.leveller, name="leveller"),
    
    # ======================== AI DOUBT SOLVER ========================
    
    path('ask-doubt/', doubt_solver.ask_doubt, name='ask_doubt'),  # Main page for doubt-solving
    path('ask-doubt/submit/', doubt_solver.ask_doubt_ajax, name='ask_doubt_ajax'),  # AJAX endpoint
    
    # ========================= PROFILE WORK =========================
    path("my_profile/", views.my_profile, name="my_profile"),
    path("edit_profile/", views.edit_profile, name="edit_profile"),
    path('upload_profile', views.upload_profile, name='upload_profile'),
    path("change_password", views.change_password, name="change_password"),
    path("delete_account", views.delete_account, name="delete_account"),
    
    # ======================== HELP DESK WORK ========================
    
    path("notifications/", views.notifications, name="notifications"),
    path("anonymous_message/", views.anonymous_message, name="anonymous_message"),
    path("new_message", views.new_message, name="new_message"),
    path("feedback", views.feedback, name="feedback"),
    
    # ======================== REFERRALS WORK ========================
    path("my-referrals/", views.my_referrals, name="my_referrals"),
    
]

# ========================================= FLAMES WORK =========================================

urlpatterns += [
    path('summer-training/', flames_views.student_flames, name='student_flames'),
    
    path("summer-training/<slug:slug>/", flames_views.my_course, name="flames_my_course"),
    path("course/<slug:slug>/registration", flames_views.view_registration, name="student_view_registration"),

    path("course/<int:id>/certificate", flames_views.view_certificate, name="student_view_certificate"),
    
    
    # ---- REGISTRATION URLS ----
    path('course/<slug:slug>/', course_views.course_detail, name='course_detail'),
    path('course/<slug:slug>/register/', course_views.student_flames_register, name='student_flames_register'),
    path('api/verify-referral-code/<str:code>/', course_views.verify_referral_code, name='verify_referral_code'),
    
    # ---- PAYMENT URLS ----
    path('payment/', include('student.payment_urls')),
    
    # path('flames/teams/create/<int:registration_id>/', flames.student_create_team, name='student_create_team'),
    # path('flames/teams/add-member/<int:team_id>/', flames.student_add_team_member, name='student_add_team_member'),
    # path('flames/teams/remove-member/<int:member_id>/', flames.student_remove_team_member, name='student_remove_team_member'),
]

urlpatterns += [
    # ======================== HACKATHON TEAM MAKER ========================
    path("hackathon/", hackathon_views.hackathon_dashboard, name="hackathon_dashboard"),
    path("hackathon/list-teams/", hackathon_views.list_teams, name="list_teams"),
    
    path("hackathon/create-team/", hackathon_views.create_team, name="create_team"),
    path("hackathon/get-all-skills/", hackathon_views.get_all_skills, name="get_all_skills"),
    
    path("hackathon/manage-team/<slug:slug>/", hackathon_views.manage_team, name="manage_team"),
    
    path("hackathon/update-team/<slug:slug>/", hackathon_views.update_team, name="update_team"),
    path("hackathon/delete-team/<int:team_id>/", hackathon_views.delete_team, name="delete_team"),
    
    path("hackathon/handle-join-request/<int:request_id>/<str:action>/", hackathon_views.handle_join_request, name="handle_join_request"),
    path("hackathon/send-join-request/<int:team_id>/", hackathon_views.send_join_request, name="send_join_request"),
    
    path("hackathon/remove-team-member/<int:team_id>/<int:member_id>/", hackathon_views.remove_team_member, name="remove_team_member"),
    
    path("hackathon/cancel-join-request/<int:request_id>/", hackathon_views.cancel_join_request, name="cancel_join_request"),
    
    path("hackathon/team/<slug:slug>/", hackathon_views.team_detail, name="team_detail"),
    
    path("hackathon/leave-team/<int:team_id>/", hackathon_views.leave_team, name="leave_team"),
    
    
    # Team Invitation URLs
    path("hackathon/search-students/", hackathon_views.search_students, name="search_students"),
    path("hackathon/send-team-invite/<int:team_id>/", hackathon_views.send_team_invite, name="send_team_invite"),
    path("hackathon/handle-team-invite/<int:invite_id>/<str:action>/", hackathon_views.handle_team_invite, name="handle_team_invite"),
    path("hackathon/cancel-team-invite/<int:invite_id>/", hackathon_views.cancel_team_invite, name="cancel_team_invite"),
]
# ========================================= BATCH WORK =========================================

urlpatterns += [
    # Fixed URLs first
    path("my_courses/", batch_views.my_batches, name="my_batches"),
    path("enroll_course/<int:id>/", batch_views.enroll_batch, name="enroll_batch"),
    path("sheet_progress/<int:sheet_id>/", batch_views.sheet_progress, name="sheet_progress"),
    path("fetch_sheet_questions/<int:id>/", batch_views.fetch_sheet_questions, name="fetch_sheet_questions"),
    path("batch_leaderboard_api/<slug:slug>", batch_views.student_fetch_batch_leaderboard, name="student_fetch_batch_leaderboard"),
    
    # Slug-based URLs last
        # path("<slug:slug>/", views.sheet , name="sheet"),

    path("sheet/<slug:slug>/", batch_views.my_sheet, name="my_sheet"),
    path("<slug:slug>/leaderboard", batch_views.student_batch_leaderboard, name="student_batch_leaderboard"),
    path("<slug:slug>/", batch_views.batch, name="batch"),  # Keep this last as it's the most generic
]

# ============================== JOVAC WORK ==============================

urlpatterns += [

    path("enroll_jovac/<slug:slug>/", jovac_views.enroll_jovac, name="student_enroll_jovac"),
    path("jovac/<slug:slug>/", jovac_views.jovac, name="student_jovac"),
    path("jovac/<slug:course_slug>/<slug:sheet_slug>", jovac_views.jovac_sheet, name="student_jovac_sheet"),
    path("jovac/tutorial/<int:id>/", jovac_views.view_jovac_tutorial, name="view_jovac_tutorial"),
    path("jovac/assignment/<int:id>/next", jovac_views.get_next_jovac_assignment, name="get_next_jovac_assignment"),


    # path("assignments", jovac_views.assignments, name="assignments"),
    path("submit_assignment/<int:assignment_id>", jovac_views.submit_assignment, name="submit_assignment"),
    path("assignments/<int:assignment_id>/submission", jovac_views.view_submission, name="view_submission"),
    path("delete_submission/<int:submission_id>", jovac_views.delete_submission, name="delete_submission"),



]

