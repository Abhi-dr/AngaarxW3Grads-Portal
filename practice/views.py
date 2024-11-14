from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import time
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


from .models import Sheet, Question, TestCase, Submission, Streak

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

def get_test_cases(question):
    """Retrieve all test cases for a specific question."""
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
    """Submit the code to Judge0 API with multiple test cases."""
    submissions = []
    
    # Create a list of all test cases for batch submission
    for test_case in test_cases:
        submissions.append({
            "source_code": source_code,
            "language_id": language_id,
            "stdin": test_case.input_data,
            "expected_output": test_case.expected_output,
            "cpu_time_limit": 1,
            "cpu_extra_time": 1
        })

    # Prepare the batch request payload
    batch_data = {
        "submissions": submissions
    }
    
    # Send a POST request with batch data
    response = requests.post(JUDGE0_URL + "/batch/", json=batch_data, headers=HEADERS)    

    if response.status_code == 201:
        
        
        # Retrieve tokens for all test cases
        tokens = [d['token'] for d in response.json()]
                
        # Check if tokens are retrieved
        if not tokens:
            print("No tokens received.")
            return []

        results = []
        for token in tokens:
            # Fetch the result of each test case
            for _ in range(10):  # Retry up to 10 times if result is in progress
                result_response = requests.get(f"{JUDGE0_URL}/{token}", headers=HEADERS)
                result = result_response.json()

                if result['status']['id'] not in (1, 2):  # Not in progress or queued
                    results.append(result)
                    break

                time.sleep(2)  # Wait for 2 seconds before checking again

        return results
    else:
        print(f"Error submitting batch request: {response.status_code} - {response.text}")
        return []
   
def process_test_case_result(status_id, output, expected_output, test_case, test_case_results):
    """Process each test case result based on the Judge0 status."""
    if status_id == 3:  # Accepted
        passed = output == expected_output
        status = "Passed" if passed else "Wrong Answer"
    elif status_id == 4:
        status = "Wrong Answer"
    elif status_id == 5:
        status = "Time Limit Exceeded"
    elif status_id == 6:
        status = "Compilation Error"
    elif status_id == 7:
        status = "Runtime Error"
    elif status_id == 8:
        status = "Memory Limit Exceeded"
    else:
        status = "Unknown Error"

    test_case_result = {
        "input": test_case.input_data,
        "expected_output": expected_output,
        "user_output": output,
        "passed": passed if status == "Passed" else False,
        "status": status
    }

    test_case_results.append(test_case_result)
    return passed if status == "Passed" else False

def update_submission_status(submission, passed_test_cases, total_test_cases):
    """Update the status and score of a submission."""
    if passed_test_cases == total_test_cases:
        submission.status = 'Accepted'
    else:
        submission.status = 'Wrong Answer'
    
    submission.score = int((passed_test_cases / total_test_cases) * 100) if total_test_cases > 0 else 0
    submission.save()
    
def run_code_against_test_cases(source_code, language_id, test_cases):
    """Run the submitted code against all test cases using batch submission."""
    test_case_results = []
    passed_test_cases = 0

    # Submit the code and retrieve results for all test cases
    results = run_code_on_judge0(source_code, language_id, test_cases)
    
    if results:
        for i, result in enumerate(results):
            test_case = test_cases[i]
            
            output = normalize_output(result.get('stdout', ''))
            expected_output = normalize_output(test_case.expected_output)
            status_id = result['status']['id']

            passed = process_test_case_result(
                status_id, output, expected_output, test_case, test_case_results
            )

            if passed:
                passed_test_cases += 1
        print(f"Test case results: {test_case_results}")
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

# ========================================== SUBMIT CODE ===============================================

@csrf_exempt
def submit_code(request, slug):
    
    start = time.time()
    
    if request.method == 'POST':
        try:
            question = Question.objects.get(slug=slug)
            user = request.user.student

            language_id = request.POST.get('language_id')
            source_code = request.POST.get('submission_code')
            
            print("LANGUAGE", language_id)
            print("SOURCE CODE", source_code)

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


# ========================================== RUN CODE AGAINST SAMPLE TEST CASES ==========================================

@csrf_exempt
def run_code(request, slug):
    if request.method == 'POST':
        try:
            
            print("FUNCTION CALLED")
            question = Question.objects.get(slug=slug)
            language_id = request.POST.get('language_id')
            source_code = request.POST.get('submission_code')
            
            print("QUESTION", question)
            print("LANGUAGE", language_id)
            print("SOURCE CODE", source_code)

            test_cases = TestCase.objects.filter(question=question, is_sample=True)

            if not test_cases:
                return JsonResponse({"error": "No test cases available for this question"}, status=400)

            test_case_results, passed_test_cases = run_code_against_test_cases(
                source_code, language_id, test_cases
            )
            

            return JsonResponse({
                "test_case_results": test_case_results,
                "passed_test_cases": passed_test_cases,
                "total_test_cases": len(test_cases)
            })

        except Question.DoesNotExist:
            return JsonResponse({"error": "Question not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)


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

