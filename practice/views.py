from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time, json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

import base64
from .models import Streak


from django.views.decorators.cache import cache_control

# Judge0 API endpoint and key
JUDGE0_URL = "https://theangaarbatch.in/judge0/submissions"
# JUDGE0_URL = "https://judge0-ce.p.rapidapi.com/submissions/"

HEADERS = {
    # "X-RapidAPI-Key": "2466ab7710mshe96d45a19b806efp1a790ajsne8eeb32a6197",  # Replace with your actual API key
    "X-RapidAPI-Host": "98.83.136.105:2358",
    # "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
    "Content-Type": "application/json"
}


from .models import Sheet, Question, TestCase, Submission, DriverCode

@login_required(login_url="login")
def practice(request):
    
    sheets = Sheet.objects.all()
    
    # fetch only those sheets which are not a part of any batch
    sheets = [sheet for sheet in sheets if not sheet.batches.exists()]
    
    parameters = {
        "sheets": sheets
    }
    
    return render(request, "practice/practice.html", parameters)

# ============================== SHEET VIEW =========================

@login_required(login_url="login")
def sheet(request, slug):
        
    sheet = get_object_or_404(Sheet, slug=slug)
    
    enabled_questions = sheet.get_enabled_questions_for_user(request.user.student)
    
    user_submissions = {
        submission.question.id: submission for submission in Submission.objects.filter(user=request.user, question__in=enabled_questions)
        }
    
    if not sheet.is_enabled:
        messages.info(request, "This sheet is not enabled.")
        return redirect('practice')

    parameters = {
        "sheet": sheet,
        "enabled_questions": enabled_questions,
        "user_submissions": user_submissions,  # Pass the submissions to the template
    }   
    
    return render(request, "practice/sheet.html", parameters)


# ========================================== PLAYGROUND ===============================================

@login_required(login_url="login")
def playground(request):
    return render(request, "student/playground.html")

@login_required(login_url="login")
def execute_code(request):
    if request.method == 'POST':
        language_id = request.POST.get('language_id')
        source_code = request.POST.get('source_code')
        input_data = request.POST.get('input_data')

        data = {
            "source_code": source_code,
            "language_id": language_id,
            "stdin": input_data,
            "cpu_time_limit": 1,
            "cpu_extra_time": 1
        }

        response = requests.post(JUDGE0_URL, json=data, headers=HEADERS)

        if response.status_code == 201:
            token = response.json().get('token')

            for _ in range(10):
                result_response = requests.get(f"{JUDGE0_URL}/{token}", headers=HEADERS)
                result = result_response.json()

                 # Check the status and get the output
                if result['status']['id'] == 3:  # Accepted
                    output = result['stdout']
                else:
                    output = result.get('stderr') or result.get('compile_output') or result.get('message')
                    
                if output:
                    return JsonResponse({"output": output, "status": result['status']['description']})

                
                time.sleep(2)
        else:
            return JsonResponse({"error": "Failed to execute code"}, status=response.status_code)
        
    return JsonResponse({"error": "Invalid request method"}, status=400)


# =====================================================================================================
# ========================================= HELPER FUNCTIONS ==========================================
# =====================================================================================================
def normalize_output(output):
    """
    Normalize output for consistent comparison by stripping extra spaces
    and normalizing newline characters.
    """
        
    if not output:
        return ""
    return output.replace("\r\n", "\n").strip()


def get_test_cases(question):
    """
    Get all test cases associated with the question.
    """
    try:
        return question.test_cases.all()
    except Exception as e:
        print(f"Error fetching test cases: {e}")
        return []


def create_submission(user, question, source_code, language_id):
    """
    Create a new submission entry in the database.
    """
    try:
        return Submission.objects.create(
            user=user,
            question=question,
            code=source_code,
            language=language_id,
            status='Pending'
        )
    except Exception as e:
        print(f"Error creating submission: {e}")
        raise Exception("Could not create submission.")


def run_code_on_judge0(source_code, language_id, test_cases, cpu_time_limit, memory_limit):
    """
    Send the code to Judge0 API for execution against multiple test cases.
    """
    # Prepare single stdin batch input for Judge0
    stdin = f"{len(test_cases)}\n"
    for test_case in test_cases:
        stdin += f"{test_case.input_data}\n"

    submission_data = {
        "source_code": source_code,
        "language_id": language_id,
        "stdin": stdin,
        "cpu_time_limit": 2,
        "wall_time_limit": 2,
        "memory_limit": memory_limit * 1000,
        "enable_per_process_and_thread_time_limit": True,
    }

    try:
        # Submit the code to Judge0
        response = requests.post(JUDGE0_URL, json=submission_data, headers=HEADERS)
        response.raise_for_status()
        
        token = response.json().get("token")
        if not token:
            return {
                "error": "No token received from Judge0.", 
                "outputs": None, 
                "token": None
            }

        print("TOKEN:", token)          
        
        while True:
            result_response = requests.get(f"{JUDGE0_URL}/{token}", headers=HEADERS)
            result = result_response.json()
            status_id = result.get("status", {}).get("id")

            if status_id not in [1, 2]:  # Not in queue or processing
                break
            time.sleep(1)

        if result.get("stderr") or result.get("compile_output"):            
            errors = {
                "error": (result.get("stderr")),
                "token": token,
            }
            
            if result.get("compile_output"):
                errors["compile_output"] = result.get("compile_output")                
            
            return errors

        # Check for runtime errors
        if result.get("status").get("id") in [5, 6]: # 5 ka mtlb TLE h
            return {
                "error": result.get("status").get("description"),
                "token": token,
            }

        # Process execution results
        outputs = result.get("stdout")
        
        outputs = [output.strip() for output in outputs.split("\n") if output.strip()]

        return {
            "outputs": outputs, 
            "token": token
            }

    except requests.exceptions.RequestException as e:
        return {
            "error": f"Cannot connect to Compiler. Error: {str(e)}",
            "outputs": None,
            "token": None,
        }
    except Exception as e:
        return {
            "error": f"Error in Run cod on judge0 function in views: {str(e)}",
            "outputs": None,
            "token": None,
        }


def process_test_case_result(inputs, outputs, expected_outputs):
    """
    Compare outputs against expected outputs and prepare detailed results.
    """
    results = []
    for input_data, expected_output, output in zip(inputs, expected_outputs, outputs):
        result = {
            "input": input_data,
            "expected_output": expected_output,
            "user_output": output,
            "passed": output == expected_output,
            "status": "Passed" if output == expected_output else "Wrong Answer"
        }
        results.append(result)
    return results


def update_submission_status(submission, passed, total, total_submission_count):
    """
    Update the submission status and score in the database.
    """
    try:
        submission.status = 'Accepted' if passed == total else 'Wrong Answer'
        
        # update streaks 
        if submission.status == 'Accepted':
            update_user_streak(submission.user)
        
        score = int(((passed / total) * 100) * (1 - 0.1 * (total_submission_count - 1)))
        submission.score = score
        submission.save()
        
        return score
                
    except Exception as e:
        print(f"Error updating submission: {e}")
        raise Exception("Could not update submission status.")


@login_required(login_url="login")
def problem(request, slug):
    """
    Render the problem page with question details and sample test cases.
    """
    try:
        question = get_object_or_404(Question, slug=slug)
        
        sheet = Sheet.objects.filter(questions=question).first()

        if sheet and not sheet.is_enabled:
            messages.info(request, "This question is in the sheet which is disabled now. Try Later.")
            return redirect('problem_set')
        
        if sheet and sheet.is_sequential:
            # Get all enabled questions for the user
            enabled_questions = sheet.get_enabled_questions_for_user(request.user)
            
            # Check if the question is enabled for the user
            if question not in enabled_questions:
                messages.info(request, "Beta jb tu paida nhi hua tha tb m URL se khelta tha. Mehnt kr 🙂")
                return redirect('sheet', slug=sheet.slug)  # You can redirect to the sheet or show an error
        
        sample_test_cases = TestCase.objects.filter(question=question, is_sample=True)
        return render(request, 'practice/problem.html', {
            'question': question,
            'sample_test_cases': sample_test_cases,
            'sheet': sheet
        })
    except Exception as e:
        print(f"Error loading problem page: {e}")
        return JsonResponse({"error": "Could not load problem."}, status=500)

# ============================================ UPDATE COINS ===============================================

def update_coin(user, score, question):
    
    # update the coins only if the user has submitted the code for the first time successfully
    if Submission.objects.filter(user=user, question=question).count() > 1:
        return
    
    if score == 100:
        user.coins += 5
    elif score >= 75:
        user.coins += 4
    elif score >= 50:
        user.coins += 3
    elif score >= 25:
        user.coins += 2
    else:
        user.coins += 1
    user.save()


# ============================================ UPDATE STREAKS =============================================


def update_user_streak(user):
    # Fetch or create the user's streak record
    streak, created = Streak.objects.get_or_create(user=user)

    # Update the streak
    streak.update_streak()


# ============================================ SUBMIT CODE ===============================================

@csrf_exempt
def submit_code(request, slug):
    """
    Handle user code submission for a problem.
    """
    
    if request.method == 'POST':      
        try:
            # Validate inputs
            question = get_object_or_404(Question, slug=slug)
            user = request.user.student            

            language_id = request.POST.get('language_id')
            source_code = request.POST.get('submission_code')

            if not language_id or not source_code:
                return JsonResponse({"error": "Missing language ID or source code."}, status=400)

            test_cases = get_test_cases(question)
            if not test_cases:
                return JsonResponse({"error": "No test cases available for this question."}, status=400)

            sheet = Sheet.objects.filter(questions=question).first()

            if sheet and not sheet.is_enabled:
                return JsonResponse({"sheet_disabled": "Sheet not enabled."}, status=400)

            # Create a submission record
            submission = create_submission(user, question, source_code, language_id)

            # Run the code and process results
            start = time.time()
            judge0_response = run_code_on_judge0(source_code, language_id, test_cases, question.cpu_time_limit, question.memory_limit)
            end = time.time()
            
            print("Time Taken:", end - start)
                        
            if judge0_response.get("error") or judge0_response.get("compile_output"):  # Any Kind of Error
                                
                result = {
                    "error": judge0_response.get("error"),
                    "token": judge0_response.get("token")
                }
                
                if judge0_response.get("compile_output"):
                                        
                    result["compile_output"] = judge0_response.get("compile_output")
                
                return JsonResponse(result, status=400)

            # Process successful outputs
            outputs = judge0_response["outputs"]
            expected_outputs = [normalize_output(tc.expected_output) for tc in test_cases]
            inputs = [tc.input_data for tc in test_cases]
            
            test_case_results = process_test_case_result(inputs, outputs, expected_outputs)
            passed_test_cases = sum(1 for result in test_case_results if result['passed'])
            
            total_submission_count = Submission.objects.filter(user=user, question=question).count()            
            # Update submission
            score = update_submission_status(submission, passed_test_cases, len(test_cases), total_submission_count)
            
            # Update user coins
            update_coin(user, score, question)            

            return JsonResponse({
                "test_case_results": test_case_results,
                "submission_id": submission.id,
                "status": submission.status,
                "score": submission.score,
                "compile_output": None,  # No compilation error
                "token": judge0_response.get("token"),
                "is_all_test_cases_passed": passed_test_cases == len(test_cases)
            })

        except Question.DoesNotExist:
            return JsonResponse({
                "error": "Question not found.",
                "token": judge0_response.get("token")
                }, status=404)
        except Exception as e:
            print(f"Error in submit code views: {e}")
            return JsonResponse({
                "error": "Error in submit code backend: " + str(e),
                "token": judge0_response.get("token")
                }, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=400)


# ============================================== DRIVER CODE FETCHING ===============================================

def get_driver_code(request, question_id, language_id):
    driver_code = DriverCode.objects.filter(question_id=question_id, language_id=language_id).first()
    if driver_code:
        return JsonResponse({"success": True, "code": driver_code.code})
    return JsonResponse({"success": False, "message": "Driver code not found.", "language id": language_id, "question id": question_id}, status=404)

# ========================================== RUN CODE AGAINST SAMPLE TEST CASES ==========================================

@csrf_exempt
def run_code(request, slug):
    if request.method == 'POST':
        try:
            question = get_object_or_404(Question, slug=slug)
            user = request.user.student
            
            data = json.loads(request.body)
            language_id = data.get('language_id')
            source_code = data.get('code')            

            if not language_id or not source_code:
                return JsonResponse({"error": "Missing language ID or source code."}, status=400)

            # Fetch sample test cases
            sample_test_cases = TestCase.objects.filter(question=question, is_sample=True)
            if not sample_test_cases:
                return JsonResponse({"error": "No sample test cases available."}, status=400)

            # Execute code against sample test cases
            judge0_response = run_code_on_judge0(
                source_code,
                language_id,
                sample_test_cases,
                question.cpu_time_limit,
                question.memory_limit
            )
                        
            if judge0_response.get("error") or judge0_response.get("compile_output"):  # Any Kind of Error
                                
                result = {
                    "error": judge0_response.get("error"),
                    "token": judge0_response.get("token")
                }
                
                if judge0_response.get("compile_output"):                    
                    result["compile_output"] = judge0_response.get("compile_output")
                
                return JsonResponse(result, status=400)

            # Process outputs
            outputs = judge0_response["outputs"]
                
            expected_outputs = [normalize_output(tc.expected_output) for tc in sample_test_cases]
            inputs = [tc.input_data for tc in sample_test_cases]

            test_case_results = process_test_case_result(inputs, outputs, expected_outputs)
                        
            return JsonResponse({
                "status": "Success",
                "test_case_results": test_case_results
            })

        except Exception as e:
            print(f"Error during code execution: {e}")
            return JsonResponse({
                "error": "Some Error Occued. Check Your Code 🙂",
                }, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=400)

# ========================================== CUSTOM INPUT ==========================================

def custom_input(request, slug):
    
    if request.method == 'POST':
        question = get_object_or_404(Question, slug=slug)
                
        data = json.loads(request.body)
        language_id = data.get('language_id')
        source_code = data.get('code')
        input_data = data.get('input')
        
        if not language_id or not source_code or not input_data:
            return JsonResponse({"error": "Missing language ID, source code, or input data."}, status=400)
        
        
        # check if test case with same input data already exists
        if question.test_cases.filter(input_data=input_data).count() > 0:            
            test_case = question.test_cases.filter(input_data=input_data).first()
        else:
            test_case = TestCase(question=question, input_data=input_data, expected_output="")
            
        judge0_response = run_code_on_judge0(
            source_code,
            language_id,
            [test_case],
            question.cpu_time_limit,
            question.memory_limit
        )
        
        if judge0_response.get("error") or judge0_response.get("compile_output"):  # Any Kind of Error
            
            result = {
                "error": judge0_response.get("error"),
                "token": judge0_response.get("token")
            }
            
            if judge0_response.get("compile_output"):
                result["compile_output"] = judge0_response.get("compile_output")
            
            return JsonResponse(result, status=400)
        
        outputs = judge0_response["outputs"]
        input_data = test_case.input_data
        
        # check if the expected output of the test case is already set
        if test_case.expected_output == "":
            print("EXPECTED OUTPUT SETTING")
            test_case.expected_output = outputs[0]
        
        
        result = {
            "input": input_data,
            "expected_output": test_case.expected_output,
        }
        
        return JsonResponse({
            "status": "Success",
            "test_case_result": result
        })
        
    return JsonResponse({"error": "Invalid request method."}, status=400)   

# ====================================================================================================
# ========================================== MY SUBMISSIONS ==========================================
# ====================================================================================================

@login_required(login_url="login")
def my_submissions(request, slug):
    question = get_object_or_404(Question, slug=slug)
    submissions = Submission.objects.filter(user=request.user.student, question=question).order_by('-submitted_at')
    
    parameters = {
        'question': question,
        'submissions': submissions
    }
    
    return render(request, 'practice/my_submissions.html', parameters)

# ========================================== PROBLEM SET ==========================================

@login_required(login_url="login")
def problem_set(request):
    
    return render(request, 'practice/problem_set.html')


@login_required(login_url="login")
def fetch_questions(request):
    
    query = request.GET.get("query", "").strip()
    questions = Question.objects.filter(is_approved=True, parent_id=-1)

    
    if query:
        questions = questions.filter(
            Q(title__icontains=query) | 
            Q(slug__icontains=query) | 
            Q(id__icontains=query)
        )
    
    data = [
        {
            "id": question.id,
            "title": question.title,
            "difficulty_level": question.difficulty_level,
            "difficulty_color": question.get_difficulty_level_color(),
            "youtube_link": question.youtube_link,
            "slug": question.slug,
            "status": question.get_user_status(request.user.student),
            "color": question.get_status_color(request.user.student)
        }
        for question in questions
    ]
    return JsonResponse({"questions": data})


# ========================================== NEXT QUESTION ==========================================

@login_required(login_url="login")
def render_next_question_in_sheet(request, sheet_id, question_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)
    current_question = get_object_or_404(Question, id=question_id)

    if current_question not in sheet.questions.all():
        messages.error(request, "This question is not a part of the sheet.")
        return redirect('sheet', slug=sheet.slug)

    # Get the next question in the sheet
    next_question = sheet.get_next_question(current_question)

    if next_question:
        # Render the next question
        return redirect('problem', slug=next_question.slug)


# ====================================================================================================
# ====================================== STUDENT QUESTION CRUD =======================================
# ====================================================================================================

@login_required(login_url="login")
def add_question(request):
    
    student_added_questions = Question.objects.filter(added_by=request.user.student)
    
    if request.method == 'POST':
        
        title = request.POST.get('title')
        scenario = request.POST.get("scenario")
        description = request.POST.get('description')
        constraints = request.POST.get('constraints')
        difficulty_level = request.POST.get('difficulty_level')
        
        question = Question(
            added_by = request.user.student,
            title=title,
            scenario=scenario,
            description=description,
            constraints=constraints,
            difficulty_level=difficulty_level
        )
        
        
        question.save()        
        
        messages.success(request, 'Problem added successfully. Add Test Cases for the problem')
        return redirect('student_add_test_case', slug=question.slug)
    
    parameters = {
        'student_added_questions': student_added_questions
    }
    
    return render(request, 'practice/add_question.html', parameters)


#=========================================== EDIT QUESTION ==========================================

@login_required(login_url="login")
def edit_question(request, slug):
    
    question = Question.objects.get(slug=slug)
    
    if question.get_approved_status() == "Approved":
        messages.info(request, "Jada URL se mt khel :)")
        return redirect("student_add_question")
    
    if request.method == 'POST':
        
        title = request.POST.get('title')
        scenario = request.POST.get("scenario")
        description = request.POST.get('description')
        constraints = request.POST.get('constraints')
        difficulty_level = request.POST.get('difficulty_level')
        
        question.title = title
        question.scenario = scenario
        question.description = description
        question.constraints = constraints
        question.difficulty_level = difficulty_level
        
        question.save()
        
        messages.success(request, 'Question updated successfully')
        return redirect('student_add_question')
    
    
    parameters = {
        "question": question
    }
    
    return render(request, "practice/edit_question.html", parameters)

# ========================================== ADD TEST CASE ==========================================

@login_required(login_url="login")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_test_case(request, slug):
    
    question = Question.objects.get(slug=slug)
    
    if request.method == 'POST':
        
        if question.test_cases.count() >= 5:
            messages.error(request, 'You can only add up to 5 test cases for a question')
            return redirect('student_add_test_case', slug=slug)
            
        
        input_data = request.POST.get('input_data')
        expected_output = request.POST.get('expected_output')
        is_sample = 'is_sample' in request.POST  # Check if the checkbox is checked
            
        test_case = TestCase(
            question=question,
            input_data=input_data,
            expected_output=expected_output,
            is_sample=is_sample
        )
        
        test_case.save()
        
        if question.test_cases.all().count() == 5:
            messages.success(request, "5 Test cases addedd successfully. Add more questions agr mn kre to!")
            return redirect("student_add_question")
        
        messages.success(request, 'Test case added successfully. Add More Test Cases')
        return redirect('student_add_test_case', slug=slug)
    
    parameters = {
        'question': question,
        'test_cases': question.test_cases.all()
    }
    
    return render(request, 'practice/add_test_case.html', parameters)

# ========================================== TEST CASES ==========================================

@login_required(login_url="login")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def test_cases(request, slug):
    
    question = Question.objects.get(slug=slug)
    
    parameters = {
        'question': question,
        'test_cases': question.test_cases.all()
    }
    
    return render(request, 'practice/test_cases.html', parameters)

# ========================================== DELETE TEST CASE ==========================================

@login_required(login_url="login")
def delete_test_case(request, id):
    
    test_case = get_object_or_404(TestCase, id=id)
    question = test_case.question
    
    test_case.delete()
    
    messages.success(request, 'Test case deleted successfully')
    return redirect('student_test_cases', slug=question.slug)


# ========================================== DELETE QUESTION ==========================================

@login_required(login_url="login")
def delete_question(request, id):
    
    question = get_object_or_404(Question, id=id)
    
    question.delete()
    
    messages.success(request, 'Question deleted successfully')
    return redirect('student_add_question')

