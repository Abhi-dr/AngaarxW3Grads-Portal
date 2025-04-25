from django.urls import path

from . import views, execution_views



urlpatterns = [
    path("", views.practice , name="practice"),
    
    path("<slug:slug>/", views.sheet , name="sheet"),
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



# if request.method == 'POST':
        
    #     language_id = request.POST.get('language_id')
    #     source_code = request.POST.get('source_code')
    #     input_data = request.POST.get('input_data')  # Get input data from the request
        
    #     # Ensure required fields are provided
    #     if not (language_id and source_code):
    #         return JsonResponse({"error": "Missing required fields (language_id, source_code)"}, status=400)

    #     # Encode source code and input data
    #     encoded_code = base64.b64encode(source_code.encode('utf-8')).decode('utf-8')
    #     encoded_input = base64.b64encode(input_data.encode('utf-8')).decode('utf-8') if input_data else None

    #     # Prepare submission payload
    #     data = {
    #         "source_code": encoded_code,
    #         "language_id": language_id,
    #         "cpu_time_limit": 1,
    #         "cpu_extra_time": 1,
    #         "base64_encoded": True,
    #         "stdin": encoded_input  # Add input data to the payload
    #     }

    #     try:
    #         response = requests.post(f"{JUDGE0_URL}?base64_encoded=true", json=data, headers=HEADERS, timeout=10)
    #         response.raise_for_status()
    #     except requests.exceptions.RequestException as e:
    #         return JsonResponse({"error": f"Request failed: {str(e)}"}, status=500)

    #     if response.status_code == 201:
    #         token = response.json().get('token')
            
    #         if not token:
    #             return JsonResponse({"error": "Failed to retrieve submission token"}, status=500)

    #         for i in range(10):  # Maximum of 10 attempts
    #             try:
    #                 result_response = requests.get(f"{JUDGE0_URL}/{token}?base64_encoded=true", headers=HEADERS, timeout=10)
    #                 result_response.raise_for_status()
    #                 result = result_response.json()
    #             except requests.exceptions.RequestException as e:
    #                 return JsonResponse({"error": f"Polling failed: {str(e)}"}, status=500)

    #             status_id = result.get('status', {}).get('id')
    #             status_description = result.get('status', {}).get('description', 'Unknown Status')

    #             if status_id == 3:  # ✅ Accepted (Successful Execution)
    #                 output = result.get('stdout')
    #                 if output:
    #                     decoded_output = base64.b64decode(output).decode('utf-8')
    #                     return JsonResponse({"output": decoded_output, "status": status_description})

    #             elif status_id in [5, 6, 7, 11]:  # ❌ Error Cases
    #                 error_output = (
    #                     result.get('stderr') or
    #                     result.get('compile_output') or
    #                     result.get('message')
    #                 )
    #                 if error_output:
    #                     decoded_error = base64.b64decode(error_output).decode('utf-8', errors='replace')
    #                     return JsonResponse({"error": decoded_error, "status": status_description})
    
    #             time.sleep(1)  # Poll every 1 second

    #         return JsonResponse({"error": "Timeout while waiting for the result"}, status=408)

    #     return JsonResponse({"error": "Failed to submit code to Judge0"}, status=response.status_code)
    
    
    
# ------------------------------- submit code ------------------------------
# start2 = time.time()
            # judge0_response = run_code_on_judge0(token)
            # end2 = time.time()
            
            # print("Time Taken to get token:", end - start)
            # print("Time Taken to get Output:", end2 - start2)
            
                        
            # if judge0_response.get("error") or judge0_response.get("compile_output"):  # Any Kind of Error
                                
            #     result = {
            #         "error": judge0_response.get("error"),
            #         "token": judge0_response.get("token")
            #     }
                
            #     update_submission_status(submission, 0, len(test_cases), 0, status="Compilation Error")
                
            #     if judge0_response.get("compile_output"):
                    
                                        
            #         result["compile_output"] = judge0_response.get("compile_output")
                
            #     return JsonResponse(result, status=400)

            # # Process successful outputs
            # outputs = judge0_response["outputs"]
            # expected_outputs = [normalize_output(tc.expected_output) for tc in test_cases]
            # inputs = [tc.input_data for tc in test_cases]
            
            # test_case_results = process_test_case_result(inputs, outputs, expected_outputs)
            # passed_test_cases = sum(1 for result in test_case_results if result['passed'])
            
            # total_submission_count = Submission.objects.filter(user=user, question=question).count()            
            # # Update submission
            # score = update_submission_status(submission, passed_test_cases, len(test_cases), total_submission_count)
            
            # # Update user coins
            # update_coin(user, score, question)            

            # return JsonResponse({
            #     "test_case_results": test_case_results,
            #     "submission_id": submission.id,
            #     "status": submission.status,
            #     "score": submission.score,
            #     "compile_output": None,  # No compilation error
            #     "token": judge0_response.get("token"),
            #     "is_all_test_cases_passed": passed_test_cases == len(test_cases)
            # })

    #     except Question.DoesNotExist:
    #         return JsonResponse({
    #             "error": "Question not found.",
    #             "token": judge0_response.get("token")
    #             }, status=404)
    #     except Exception as e:
    #         print(f"Error in submit code views: {e}")
    #         return JsonResponse({
    #             "error": "Error in submit code backend: " + str(e),
    #             "token": judge0_response.get("token")
    #             }, status=400)

    # return JsonResponse({"error": "Invalid request method."}, status=400)
