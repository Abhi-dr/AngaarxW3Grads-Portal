from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import Administrator
from django.http import JsonResponse
import requests, time, re, json, base64
from django.db import transaction

from django.views.decorators.csrf import csrf_exempt

from practice.models import POD, Question, Sheet, Submission, TestCase, DriverCode, RecommendedQuestions
from django.views.decorators.cache import cache_control
from angaar_hai.custom_decorators import admin_required


import datetime


LANGUAGE_IDS = {
    'C': 50,
    'C++': 54,
    'Java': 62,
    'Python': 71
}

# ======================================== PROBLEMS ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def administrator_problems(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    unapproved_question_number = Question.objects.filter(is_approved=False).count()
    
    parameters = {
        'administrator': administrator,
        'unapproved_question_number': unapproved_question_number
    }
    return render(request, 'administration/practice/administrator_problems.html', parameters)

# ======================================== FETCH PROBLEMS ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def fetch_problems(request):
    
    query = request.GET.get("query", "").strip()
    questions = Question.objects.filter(is_approved=True).order_by('-id')   

    
    if query:
        questions = questions.filter(
            Q(title__icontains=query) | 
            Q(slug__icontains=query) | 
            Q(id__icontains=query)
        )
        
    question_list = [{
        "id": q.id,
        "title": q.title,
        "slug": q.slug,
        "difficulty_level": q.difficulty_level,
        "difficulty_color": q.get_difficulty_level_color(),
        "description": q.description,
        "cpu_time_limit": q.cpu_time_limit,
        "memory_limit": q.memory_limit,
        "test_cases_count": q.test_cases.count(),
        "submission_count": q.how_many_users_solved(),
        "status": "Active",  # Example status
        "color": "success",  # Example color
        "sheets": [{"name": sheet.name} for sheet in q.sheets.all()],
    } for q in questions]
    return JsonResponse({
            "questions": question_list,
            "total_questions": questions.count()
         })

# ======================================== ADD PROBLEM ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_question(request):
    sheets = Sheet.objects.all().order_by('-id')

    if request.method == 'POST':
        sheet = request.POST.getlist('sheet')
        title = request.POST.get('title')
        scenario = request.POST.get('scenario')
        description = request.POST.get('description')
        input_format = request.POST.get('input_format')
        output_format = request.POST.get('output_format')
        constraints = request.POST.get('constraints')
        hint = request.POST.get('hint')
        difficulty_level = request.POST.get('difficulty_level')

        description = convert_backticks_to_code(description)

        # Save the main question
        question = Question.objects.create(
            title=title,
            scenario=scenario,
            description=description,
            input_format=input_format,
            output_format=output_format,
            constraints=constraints,
            hint=hint,
            difficulty_level=difficulty_level,
            is_approved=True
        )
        question.save()

        try:
            recommended_questions_data = json.loads(request.POST.get('recommended_questions', '[]'))
            
            if isinstance(recommended_questions_data, list):
                recommended_questions = [
                    RecommendedQuestions(
                        question=question,
                        title=rq["title"],
                        platform=rq["platform"],
                        link=rq["link"]
                    ) for rq in recommended_questions_data
                ]
                RecommendedQuestions.objects.bulk_create(recommended_questions)

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON data"}, status=400)

        return JsonResponse({"success": True, "message": "Question added successfully!"})

    return render(request, 'administration/practice/add_question.html', {'sheets': sheets})


# ======================================== DELETE PROBLEM ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_question(request, id):
    
    question = Question.objects.get(id=id)
    
    question.delete()
    
    messages.success(request, 'Problem deleted successfully')
    return redirect('administrator_problems')


# ======================================== EDIT PROBLEM ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_question(request, id):
    
    administrator = Administrator.objects.get(id=request.user.id)
    question = Question.objects.get(id=id)
    sheets = Sheet.objects.all().order_by('-id')
    
    if request.method == 'POST':
        
        sheet = request.POST.getlist('sheet')
        title = request.POST.get('title')
        scenario = request.POST.get('scenario')
        description = request.POST.get('description')
        input_format = request.POST.get('input_format')
        output_format = request.POST.get('output_format')
        constraints = request.POST.get('constraints')
        hint = request.POST.get('hint')
        difficulty_level = request.POST.get('difficulty_level')
        position = request.POST.get('position')
        cpu_time_limit = request.POST.get('cpu_time_limit')
        memory_limit = request.POST.get('memory_limit')
        
        description = convert_backticks_to_code(description)

        
        question.title = title
        question.description = description
        question.scenario = scenario
        question.input_format = input_format
        question.output_format = output_format
        question.constraints = constraints
        question.hint = hint
        question.difficulty_level = difficulty_level
        question.position = position
        question.cpu_time_limit = float(cpu_time_limit)
        question.memory_limit = int(memory_limit)
        
        question.save()
        
        question.sheets.clear()
        
        for sheet_id in sheet:
            sheet = Sheet.objects.get(id=sheet_id)
            question.sheets.add(sheet)
        
        messages.success(request, 'Problem updated successfully')
        return redirect('edit_question', id=question.id)
    
    question.description = convert_code_to_backticks(question.description)
    
    parameters = {
        'administrator': administrator,
        'question': question,
        'sheets': sheets
    }
    return render(request, 'administration/practice/edit_question.html', parameters)


# ======================================== QUESTION REQUESTS ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def question_requests(request):
        
    administrator = Administrator.objects.get(id=request.user.id)
    
    questions = Question.objects.filter(is_approved=False)
    
    parameters = {
        'administrator': administrator,
        'questions': questions
    }
    return render(request, 'administration/practice/question_requests.html', parameters)

# ======================================== APPROVE REQUESTS =======================================

@login_required(login_url="login")
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def approve_question(request, id):
    
    if request.method == 'POST':
        question = Question.objects.get(id=id)
        question.is_approved = True
        question.save()
        
        return JsonResponse({
                "success": True, 
                "message": "This question has been approved successfully!"
                })

    return redirect("question_requests")

@login_required(login_url="login")
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def reject_question(request, id):
    if request.method == 'POST':
        question = Question.objects.get(id=id)
        question.delete()
        
        # Send a JSON response for AJAX requests
        return JsonResponse({"success": True, "message": "This question has been rejected successfully!"})

    # Fallback for non-AJAX requests
    messages.success(request, "This question has been rejected successfully!")
    return redirect("question_requests")


# ======================================== TEST CASES ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def test_cases(request, slug):
    
    administrator = Administrator.objects.get(id=request.user.id)
    
    question = Question.objects.get(slug=slug)
    
    test_cases = TestCase.objects.filter(question=question)
    
    parameters = {
        'administrator': administrator,
        'question': question,
        'test_cases': test_cases
    }
    return render(request, 'administration/practice/test_cases.html', parameters)


# ======================================== ADD TEST CASE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_test_case(request, slug):
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        question = Question.objects.get(slug=slug)
        
        input_data = request.POST.get('input_data')
        expected_output = request.POST.get('expected_output')
        explaination = request.POST.get('explaination', "-")
        is_sample = 'is_sample' in request.POST
        
        test_case = TestCase(
            question=question,
            input_data=input_data,
            expected_output=expected_output,
            explaination=explaination,
            is_sample=is_sample
        )
        test_case.save()
        
        # Return the newly added test case as JSON
        return JsonResponse({
            'status': 'success',
            'message': 'Test case added successfully.',
            'test_case': {
                'id': test_case.id,
                'input_data': test_case.input_data,
                'expected_output': test_case.expected_output,
                'is_sample': test_case.is_sample
            }
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)

# ======================================= ADD TEST CASES USING JSON ============================


def add_test_cases(request, slug):
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        question = Question.objects.get(slug=slug)
        
        json_data = request.POST.get("json_data")
        
        try:
        # Parse the JSON data
            data = json.loads(json_data)
            if not isinstance(data, dict):
                print("JSON should be a dictionary with numeric keys.")
                return JsonResponse({
                    "message": "The data should be in JSON format only"
                })
            
            # Prepare TestCase objects for bulk creation
            test_cases = [  
                TestCase(
                    question = question,
                    input_data=value.get('Input'), 
                    expected_output=value.get('Output')
                    ) for key, value in data.items() if isinstance(value, dict) and 'Input' in value and 'Output' in value
            ]
            

            
            # Use bulk_create within a transaction for efficiency
            with transaction.atomic():
                TestCase.objects.bulk_create(test_cases, ignore_conflicts=True)  # Prevent duplicate key errors

            return JsonResponse({
                    'status': 'success',
                    'message': 'Test case added successfully.'
                })
    

        except json.JSONDecodeError:
            return JsonResponse({
                    "message": "Invalid JSON Format. The data should be in JSON format only"
                })
        except Exception as e:
            return JsonResponse({
                    "message": "API Error:" + str(e)
                })
        
        # Return the newly added test case as JSON



# ======================================== EDIT TEST CASE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_test_case(request, id):
    
    administrator = Administrator.objects.get(id=request.user.id)
    
    test_case = TestCase.objects.get(id=id)
    
    if request.method == 'POST':
        
        input_data = request.POST.get('input_data')
        expected_output = request.POST.get('expected_output')
        explaination = request.POST.get('explaination', "-")
        is_sample = 'is_sample' in request.POST
                
        test_case.input_data = input_data
        test_case.expected_output = expected_output
        test_case.explaination = explaination
        test_case.is_sample = is_sample

        test_case.save()
        
        
        messages.success(request, 'Test case updated successfully')
        return redirect('test_cases', slug=test_case.question.slug)
    
    parameters = {
        'administrator': administrator,
        'test_case': test_case
    }
    
    return render(request, 'administration/practice/edit_test_case.html', parameters)

# ======================================== DELETE TEST CASE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_test_case(request, id):
    
    test_case = TestCase.objects.get(id=id)
    
    test_case.delete()
    
    messages.success(request, 'Test case deleted successfully')
    return redirect('test_cases', slug=test_case.question.slug)


# ======================================== DRIVER CODE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def driver_code(request, slug):
    
    administrator = Administrator.objects.get(id=request.user.id)
    question = Question.objects.get(slug=slug)
    
    driver_codes = {code.language_id: code.code for code in DriverCode.objects.filter(question=question)}
    
        
    if request.method == 'POST':
        
        language_id = request.POST.get('language_id')
        code = request.POST.get('code')

        # Check if a driver code already exists for the given language
        existing_code = DriverCode.objects.filter(question=question, language_id=language_id).first()
        if existing_code:
            existing_code.code = code
            existing_code.save()
            return JsonResponse({"success": True, "message": f"Driver code for {question.title} updated successfully."})
        else:
            driver_code = DriverCode(question=question, language_id=language_id, code=code)
            driver_code.save()
            return JsonResponse({"success": True, "message": f"Driver code for {question.title} added successfully."})

    parameters = {
        "administrator": administrator,
        'question': question,
        'driver_codes': driver_codes
    }

    return render(request, 'administration/practice/driver_code.html', parameters)


# ================================================================================================
# ============================================ POD WORK ==========================================
# ================================================================================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def administrator_pod(request):
    administrator = Administrator.objects.get(id=request.user.id)
    
    pods = POD.objects.filter(date__lte=datetime.date.today()).order_by('-date')
    
    parameters = {
        "administrator": administrator,
        "pods": pods
    }

    return render(request, "administration/practice/administrator_pod.html", parameters)


# =========================================== SET POD PAGE ================================


@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def set_pod(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    questions = Question.objects.filter(pods__isnull=True)
    
    parameters = {
        "administrator": administrator,
        "questions": questions
    }

    return render(request, 'administration/practice/set_pod.html', parameters)


# ================================================ SAVE POD ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def save_pod(request, id):
    
    date = request.POST.get('pod_date')
    
    
    if date:
        
        question = Question.objects.get(id=id)
        pod, created = POD.objects.get_or_create(question=question, date=date)
                
        if created:
            messages.success(request, 'POD set successfully')
        else:
            messages.info(request, 'POD already exists for this date')
            
        return redirect('set_pod')
    
    else:
        messages.error(request, 'Please select a date')
            
    return redirect('set_pod')


# ================================================================================================
# ========================================= TEST CODE ============================================
# ================================================================================================

JUDGE0_URL = "https://theangaarbatch.in/judge0/submissions"

HEADERS = {
    "X-RapidAPI-Host": "98.83.136.105:2358",
    "Content-Type": "application/json"
}

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def test_code(request, slug):
    
    administrator = Administrator.objects.get(id=request.user.id)
    question = get_object_or_404(Question, slug=slug)
    sample_test_cases = TestCase.objects.filter(question=question, is_sample=True)
    
    parameters = {
        'administrator': administrator,
        'question': question,
        'sample_test_cases': sample_test_cases
    }
    
    return render(request, 'administration/practice/test_code.html', parameters)


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


def run_code_on_judge0(source_code, language_id, test_cases, cpu_time_limit, memory_limit):
    """
    Send the code to Judge0 API for execution against multiple test cases.
    """
    # Prepare single stdin batch input for Judge0
    stdin = f"{len(test_cases)}\n"
    for test_case in test_cases:
        stdin += f"{test_case.input_data}\n"
        
    encoded_code = base64.b64encode(source_code.encode('utf-8')).decode('utf-8')
    encoded_stdin = base64.b64encode(stdin.encode('utf-8')).decode('utf-8')

    submission_data = {
        "source_code": encoded_code,
        "language_id": language_id,
        "stdin": encoded_stdin,
        "cpu_time_limit": cpu_time_limit,
        "wall_time_limit": cpu_time_limit,
        "memory_limit": memory_limit * 1000,
        "enable_per_process_and_thread_time_limit": True,
        "base64_encoded": True  # Critical flag to let Judge0 know the code is Base64-encoded
    }

    try:
        # 📝 Submit Code to Judge0
        response = requests.post(JUDGE0_URL + "?base64_encoded=true", json=submission_data, headers=HEADERS)
        response.raise_for_status()
        
        token = response.json().get("token")
        if not token:
            return {"error": "No token received from Judge0.", "outputs": None, "token": None}

        print("✅ TOKEN:", token)
        
        while True:
            result_response = requests.get(f"{JUDGE0_URL}/{token}?base64_encoded=true", headers=HEADERS)
            result = result_response.json()
            status_id = result.get("status", {}).get("id")

            if status_id not in [1, 2]:  # Finished Processing
                break
            time.sleep(1)
            

        # ❗ Handle Errors
        if result.get("stderr"):
            stderr = base64.b64decode(result['stderr']).decode('utf-8', errors='replace')
            return {"error": f"Runtime Error: {stderr}", "token": token}

        if result.get("compile_output"):
            compile_output = base64.b64decode(result['compile_output']).decode('utf-8', errors='replace')
            return {"error": f"Compile Error: {compile_output}", "token": token}

        if result.get("status", {}).get("id") == 5:
            return {"error": "Time Limit Exceeded (TLE)", "token": token}

        if result.get("status", {}).get("id") == 6:
            return {"error": "Compilation Error", "token": token}

        # ✅ Decode Outputs
        outputs = result.get("stdout", "")
        if outputs:
            outputs = base64.b64decode(outputs).decode('utf-8', errors='replace')
            outputs = [output.strip() for output in outputs.split("\n") if output.strip()]
        else:
            outputs = ["No output generated."]

        return {"outputs": outputs, "token": token}

    except requests.exceptions.RequestException as e:
        return {"error": f"Request Error: {str(e)}", "outputs": None, "token": None}
    except Exception as e:
        return {"error": f"Unexpected Error: {str(e)}", "outputs": None, "token": None}


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


@csrf_exempt
def submit_code(request, slug):
    """
    Handle user code submission for a problem.
    """
    
    if request.method == 'POST':      
        try:
            # Validate inputs
            question = get_object_or_404(Question, slug=slug)

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

            return JsonResponse({
                "test_case_results": test_case_results,
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


# ========================================== Convert to code ==========================================

def convert_backticks_to_code(text):
    pattern = r"`(.*?)`"
    result = re.sub(pattern, r"<code style='font-size: 110%'>\1</code>", text)
    return result


def convert_code_to_backticks(text):

    pattern = r"<code style='font-size: 110%'>(.*?)</code>"

    result = re.sub(pattern, r"`\1`", text)
    return result
