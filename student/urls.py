from django.urls import path
from . import batch_views, views, doubt_solver, hackathon_views

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
    
    path("hackathon/cancel-join-request/<int:request_id>/", hackathon_views.cancel_join_request, name="cancel_join_request"),
    
    path("hackathon/team/<int:team_id>/", hackathon_views.team_detail, name="team_detail"),
    path("hackathon/remove-team-member/<int:team_id>/<int:member_id>/", hackathon_views.remove_team_member, name="remove_team_member"),
    
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
    path("sheet/<slug:slug>/", batch_views.my_sheet, name="my_sheet"),
    path("<slug:slug>/leaderboard", batch_views.student_batch_leaderboard, name="student_batch_leaderboard"),
    path("<slug:slug>/", batch_views.batch, name="batch"),  # Keep this last as it's the most generic
]
