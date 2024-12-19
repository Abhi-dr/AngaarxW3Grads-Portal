from django.urls import path, include
from . import sheet_views, views

urlpatterns = [

    path("", views.index, name="instructor"),


    # ========================= PROFILE WORK =========================

    path("instructor_profile/", views.instructor_profile, name="instructor_profile"),
    path("edit_instructor_profile/", views.edit_instructor_profile, name="edit_instructor_profile"),
    path('upload_instructor_profile', views.upload_instructor_profile, name='upload_instructor_profile'),
    path("change_instructor_password", views.change_instructor_password, name="change_instructor_password"),

    # ============================ TEST CASES WORK ==========================

    path("test_cases/<slug:slug>/", sheet_views.test_cases, name="instructor_test_cases"),
    path("add_test_case/<slug:slug>/", sheet_views.add_test_case, name="instructor_add_test_case"),
    path("delete_test_case/<int:id>/", sheet_views.delete_test_case, name="instructor_delete_test_case"),
    path("edit_test_case/<int:id>/", sheet_views.edit_test_case, name="instructor_edit_test_case"),
    
    path("driver_code/<slug:slug>/", sheet_views.driver_code, name="instructor_driver_code"),
    
    path("test_code/<slug:slug>/", sheet_views.test_code, name="instructor_test_code"),


    # ========================= SHEET WORK ==========================
    path("edit_instructor_profile/", views.edit_instructor_profile, name="edit_instructor_profile"),

    path("sheets/", sheet_views.sheets, name="instructor_sheets"),
    path("add_sheet/", sheet_views.add_sheet, name="instructor_add_sheet"),
    path("sheet/<slug:slug>/edit/", sheet_views.edit_sheet, name="instructor_edit_sheet"),
    path("delete_sheet/<int:id>/", sheet_views.delete_sheet, name="instructor_delete_sheet"),
    path("sheet/<slug:slug>/", sheet_views.sheet, name="instructor_sheet"),
    path("get_excluded_questions/<int:sheet_id>/", sheet_views.get_excluded_questions, name="get_excluded_questions"),
    
    path("remove_question_from_sheet/<int:sheet_id>/<int:question_id>/", sheet_views.remove_question_from_sheet, name="instructor_remove_from_sheet"),
    
    path("make_duplicate/<int:sheet_id>/<int:question_id>/", sheet_views.make_duplicate, name="instructor_make_duplicate"),
    path("add_new_question/<slug:slug>/", sheet_views.add_new_question, name="instructor_add_new_question"),
    
    path("leaderboard/<slug:slug>", sheet_views.leaderboard, name="instructor_leaderboard"),
    path("sheet_leaderboard/<slug:slug>", sheet_views.sheet_leaderboard, name="instructor_sheet_leaderboard"),
    
    path("reorder/<slug:slug>/", sheet_views.reorder, name="instructor_reorder"),
    path('update-sheet-order/<int:sheet_id>/', sheet_views.update_sheet_order, name='update_sheet_order'),

    path("instructor_set_sheet_timer/<int:sheet_id>/", sheet_views.set_sheet_timer, name="instructor_set_sheet_timer"),
    path("fetch_sheet_timer/<int:sheet_id>/", sheet_views.fetch_sheet_timer, name="fetch_sheet_timer"),
    
    path('download-leaderboard/<slug:slug>/', sheet_views.download_leaderboard_excel, name='download_leaderboard'),
    
    path("delete_question/<int:id>", sheet_views.delete_question, name="instructor_delete_question"),
    path("edit_question/<int:id>", sheet_views.edit_question, name="instructor_edit_question"),
    
    path("test_code/<slug:slug>/", sheet_views.test_code, name="instructor_test_code"),

    
    # ====================================== ENABLE / DISABLE SHEET ===================================
    
    path('sheet/<slug:slug>/toggle-status/', sheet_views.toggle_sheet_status, name='toggle_sheet_status'),
]

