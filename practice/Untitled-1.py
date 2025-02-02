
def get_test_cases(question):
    return question.test_cases.all()

def create_submission(user, question, source_code, language_id):
    """Create a submission entry for the user."""
    return Submission.objects.create(
        user=user,
        question=question,
        code=source_code,
        language=language_id,
        status='Pending'
    )

def run_code_on_judge0(source_code, language_id, test_cases):    
    stdin = f"{len(test_cases)}\n"
    
    for test_case in test_cases:
        stdin += f"{test_case.input_data}\n"
    
    submission = {
        "source_code": source_code,
        "language_id": language_id,
        "stdin": stdin,
        "cpu_time_limit": 1,
        "cpu_extra_time": 1
    }

    response = requests.post(JUDGE0_URL, json=submission, headers=HEADERS)
        
    token = response.json().get('token')
    
    if response.status_code != 201:
        print(f"Error submitting batch: {response.status_code}, {response.text}")
        return []
    
    response = requests.get(f"{JUDGE0_URL}/{token}", headers=HEADERS)
    
    result = response.json()
    
    print("RESULT", result, end="\n\n")
    
    outputs = result.get('stdout', '')    
    
    outputs = outputs.split("\n")
    outputs.pop()
        
    return outputs

   
def process_test_case_result(inputs, outputs, expected_output):    
    test_case_results = []
    
    for input, expected_output, output in zip(inputs, expected_output, outputs): 
        
        test_case_result = {
            "input": input,
            "expected_output": expected_output,
            "user_output": output,
            "passed": "Passed" if output == expected_output else "Wrong Answer",
            "status": "Passed" if output == expected_output else "Wrong Answer"
        }

        test_case_results.append(test_case_result)
    
    return test_case_results
        

def update_submission_status(submission, passed_test_cases, total_test_cases):
    """Update the status and score of a submission."""
    if passed_test_cases == total_test_cases:
        submission.status = 'Accepted'
    else:
        submission.status = 'Wrong Answer'
    
    submission.score = int((passed_test_cases / total_test_cases) * 100) if total_test_cases > 0 else 0
    submission.save()
    
def run_code_against_test_cases(source_code, language_id, test_cases):
    passed_test_cases = 0

    # Submit the code and retrieve results for all test cases
    outputs = run_code_on_judge0(source_code, language_id, test_cases)
    expected_outputs = [output.expected_output for output in test_cases]
    
    inputs = [normalize_output(output.input_data) for output in test_cases]

    print("EXPECTED OUTPUTS", expected_outputs)
    
    if outputs:

        test_case_results = process_test_case_result(
            inputs, outputs, expected_outputs
        )
        
        passed_test_cases = sum(
            1 for test_case in test_case_results if test_case['passed'] == 'Passed'
        )
        
        print(f"-----------------------------Passed test cases: {passed_test_cases}")
                
    else:
        print("No results were retrieved.")

    return test_case_results, passed_test_cases

def normalize_output(output):
    
    if not output:
        return output    
    return output.replace('\r\n', '\n').strip()

# ======================================================================================================
# ========================================= PROBLEM SUBMISSION =========================================
# ======================================================================================================

@login_required(login_url="login")
def problem(request, slug):
    
    question = get_object_or_404(Question, slug=slug)
    sample_test_cases = TestCase.objects.filter(question=question, is_sample=True)
    
    parameters = {
        'question': question,
        'sample_test_cases': sample_test_cases,
    }
    return render(request, 'practice/problem.html', parameters)



@csrf_exempt
def submit_code(request, slug):
    
    start = time.time()
    
    if request.method == 'POST':
        try:
            question = Question.objects.get(slug=slug)
            user = request.user.student

            language_id = request.POST.get('language_id')
            source_code = request.POST.get('submission_code')

            test_cases = get_test_cases(question)

            # Handle submission creation and validation
            submission = create_submission(user, question, source_code, language_id)
            if not test_cases:
                return JsonResponse({"error": "No test cases available for this question"}, status=400)

            # Run code against test cases and process results
            test_case_results, passed_test_cases = run_code_against_test_cases(
                source_code, language_id, test_cases
            )

            # Update submission status and score
            update_submission_status(submission, passed_test_cases, len(test_cases))
            
            end = time.time()
            
            print(end - start)

            print(submission.status)

            return JsonResponse({
                "test_case_results": test_case_results,
                "submission_id": submission.id,
                "status": submission.status,
                "score": submission.score
            })

        except Question.DoesNotExist:
            return JsonResponse({"error": "Question not found"}, status=404)
        except Exception as e:
            print(f"Error: {str(e)}")  # Debugging error
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

