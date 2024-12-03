from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time, json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

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
    
    questions = sheet.questions.filter(is_approved=True)
    
    user_submissions = {
        submission.question.id: submission for submission in Submission.objects.filter(user=request.user, question__in=questions)
        }

    parameters = {
        "sheet": sheet,
        "questions": questions,
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
        
        token = response.json().get('token')
        
        print("TOKEN", token)
        
        if not token:
            raise Exception("No token received from Judge0.")
        
        # Fetch results
        result_response = requests.get(f"{JUDGE0_URL}/{token}", headers=HEADERS)
        
        while result_response.json().get("status").get("id") == 2:  # Status 'In Queue'
            time.sleep(1)
            result_response = requests.get(f"{JUDGE0_URL}/{token}", headers=HEADERS)

        result = result_response.json()
                
        if result.get("compile_output"):
            return {
            "error": result["compile_output"].strip(),
            "outputs": None,
            "token": token
        }

        # Check for runtime errors
        if result.get("stderr"):
            return {
                "error": result["stderr"].strip(),
                "outputs": None,
                "token": token
            }
        
        # Process execution results
        outputs = result.get('stdout', '')
        outputs = [output.strip() for output in outputs.split("\n")]
        
        return {
        "error": None,
        "outputs": outputs,
        "token": token
    }

    except requests.exceptions.RequestException as e:
        print(f"Judge0 API error: {e}")
        return {
            "error": "Cannot connect to Compier \n Error: " + str(e),
        }
    except Exception as e:
        print(f"Error during code execution with token {token}: {e}")
        return {
            "error": result.get("status").get("description"),
            "outputs": None,
            "token": token
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


def update_submission_status(submission, passed, total):
    """
    Update the submission status and score in the database.
    """
    try:
        submission.status = 'Accepted' if passed == total else 'Wrong Answer'
        submission.score = int((passed / total) * 100) if total > 0 else 0
        submission.save()
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
        sample_test_cases = TestCase.objects.filter(question=question, is_sample=True)
        return render(request, 'practice/problem.html', {
            'question': question,
            'sample_test_cases': sample_test_cases
        })
    except Exception as e:
        print(f"Error loading problem page: {e}")
        return JsonResponse({"error": "Could not load problem."}, status=500)

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

            # Create a submission record
            submission = create_submission(user, question, source_code, language_id)

            # Run the code and process results
            start = time.time()
            judge0_response = run_code_on_judge0(source_code, language_id, test_cases, question.cpu_time_limit, question.memory_limit)
            end = time.time()
            
            print("Time Taken:", end - start)
            
            if judge0_response["error"]:  # Compilation error
                update_submission_status(submission, 0, len(test_cases))  # Mark all as failed
                return JsonResponse({
                    "submission_id": submission.id,
                    "status": "Compilation Error",
                    "score": 0,
                    "compiler_output": judge0_response["error"],
                    "token": judge0_response.get("token")
                })

            # Process successful outputs
            outputs = judge0_response["outputs"]
            expected_outputs = [normalize_output(tc.expected_output) for tc in test_cases]
            inputs = [tc.input_data for tc in test_cases]
            
            test_case_results = process_test_case_result(inputs, outputs, expected_outputs)
            passed_test_cases = sum(1 for result in test_case_results if result['passed'])

            # Update submission
            update_submission_status(submission, passed_test_cases, len(test_cases))

            return JsonResponse({
                "test_case_results": test_case_results,
                "submission_id": submission.id,
                "status": submission.status,
                "score": submission.score,
                "compile_output": None,  # No compilation error
                "token": judge0_response.get("token")
            })

        except Question.DoesNotExist:
            return JsonResponse({
                "error": "Question not found.",
                "token": judge0_response.get("token")
                }, status=404)
        except Exception as e:
            print(f"Error during submission: {e}")
            return JsonResponse({
                "error": "An unexpected error occurred.",
                "token": judge0_response.get("token")
                }, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=400)


# ============================================== DRIVER CODE FETCHING ===============================================

def get_driver_code(request, question_id, language_id):
    driver_code = DriverCode.objects.filter(question_id=question_id, language_id=language_id).first()
    if driver_code:
        return JsonResponse({"success": True, "code": driver_code.code})
    return JsonResponse({"success": False, "message": "Driver code not found."}, status=404)

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
            
            if judge0_response["error"]:
                return JsonResponse({
                    "status": "Error",
                    "compiler_output": judge0_response["error"]
                })

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
            return JsonResponse({"error": "An unexpected error occurred."}, status=500)

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
    questions = Question.objects.filter(is_approved=True)

    
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
# get next question of the current sheet but not in json
def next_question(request, slug):
    
    sheet = get_object_or_404(Sheet, slug=slug)
    questions = sheet.questions.filter(is_approved=True)
    
    user_submissions = {
        submission.question.id: submission for submission in Submission.objects.filter(user=request.user, question__in=questions)
        }
    
    # Get the next question that has not been attempted yet
    for question in questions:
        if question.id not in user_submissions:
            return redirect('problem', slug=question.slug)
    
    messages.info(request, "You have completed all questions in this sheet.")
    return redirect('sheet', slug=sheet.slug)

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

