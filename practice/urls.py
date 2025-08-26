from django.urls import path

from . import views, execution_views



urlpatterns = [
    path("", views.practice , name="practice"),
    
    # path("<slug:slug>/", views.sheet , name="sheet"),
    path("playground", views.playground, name="playground"),
    
    path("my_submissions/<slug:slug>/", views.my_submissions, name="my_submissions"),
    
    path("problem_set", views.problem_set, name="problem_set"),
    path("fetch_questions", views.fetch_questions, name="fetch_questions"),

    
    path("fetch_recommended_questions/<slug:slug>", views.fetch_recommended_questions, name="fetch_recommended_questions"),

    
    # path("submission/<slug:slug>/", views.submission, name="submission"),
    
    # ============================== QUESTION CRUD =========================
    
    path("add_question", views.add_question, name="student_add_question"),
    path("edit_question/<slug:slug>", views.edit_question, name="student_edit_question"),
    path("add_test_case/<slug:slug>/", views.add_test_case, name="student_add_test_case"),
    path("test_cases/<slug:slug>/", views.test_cases, name="student_test_cases"),
    path("delete_test_case/<int:id>/", views.delete_test_case, name="student_delete_test_case"),
    path("delete_question/<int:id>/", views.delete_question, name="student_delete_question"),

]


urlpatterns += [
    path("execute_code", execution_views.execute_code, name="execute_code"),
    path("run_code/<slug:slug>/", execution_views.run_code, name="run_code"),
    path("run_code_result/<str:token>/<slug:slug>/", execution_views.run_code_result, name="run_code_result"),
    
    path('submit_code/<slug:slug>/', execution_views.submit_code, name='submit_code'),
    path("send_output/<str:token>/<slug:slug>/", execution_views.send_output, name="send_output"),
    
    
    
    path("custom_input/<slug:slug>/", execution_views.custom_input, name="custom_input"),
    
    path("problem/<slug:slug>/", execution_views.problem, name="problem"),
    path("get-driver-code/<int:question_id>/<int:language_id>", execution_views.get_driver_code, name='get_driver_code'),
    path('unlock-hint/<int:question_id>/', execution_views.unlock_hint, name='unlock_hint'),
    
    path('render_next_question_in_sheet/<int:sheet_id>/<int:question_id>/', execution_views.render_next_question_in_sheet, name='render_next_question_in_sheet'),

]


