from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import Instructor
from django.http import JsonResponse



from practice.models import POD, Question, Sheet, Submission, TestCase
from django.views.decorators.cache import cache_control


import datetime
# ======================================== PROBLEMS ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def instructor_problems(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    unapproved_question_number = Question.objects.filter(is_approved=False).count()
    
    parameters = {
        'instructor': instructor,
        'unapproved_question_number': unapproved_question_number
    }
    return render(request, 'administration/practice/instructor_problems.html', parameters)

# ======================================== FETCH PROBLEMS ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def fetch_problems(request):
    
    query = request.GET.get("query", "").strip()
    questions = Question.objects.filter(is_approved=True)

    
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
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_question(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    sheets = Sheet.objects.all()
    
    if request.method == 'POST':
        
        sheet = request.POST.getlist('sheet')
        title = request.POST.get('title')
        description = request.POST.get('description')
        constraints = request.POST.get('constraints')
        difficulty_level = request.POST.get('difficulty_level')
        driver_code = request.POST.get('driver_code')
        
        question = Question(
            title=title,
            description=description,
            difficulty_level=difficulty_level,
            driver_code=driver_code,
            is_approved=True
        )
        
        question.save()
        
        for sheet_id in sheet:
            sheet = Sheet.objects.get(id=sheet_id)
            question.sheets.add(sheet)
        
        
        
        messages.success(request, 'Problem added successfully. Add Test Cases for the problem')
        return redirect('add_test_case', slug=question.slug)
    
    parameters = {
        'instructor': instructor,
        'sheets': sheets
    }
    return render(request, 'administration/practice/add_question.html', parameters)


# ======================================== DELETE PROBLEM ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_question(request, id):
    
    question = Question.objects.get(id=id)
    
    question.delete()
    
    messages.success(request, 'Problem deleted successfully')
    return redirect('instructor_problems')


# ======================================== EDIT PROBLEM ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_question(request, id):
    
    instructor = Instructor.objects.get(id=request.user.id)
    question = Question.objects.get(id=id)
    sheets = Sheet.objects.all()
    
    if request.method == 'POST':
        
        sheet = request.POST.getlist('sheet')
        title = request.POST.get('title')
        description = request.POST.get('description')
        difficulty_level = request.POST.get('difficulty_level')
        position = request.POST.get('position')
        cpu_time_limit = request.POST.get('cpu_time_limit')
        memory_limit = request.POST.get('memory_limit')
        
        question.title = title
        question.description = description
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
        return redirect('instructor_problems')
    
    parameters = {
        'instructor': instructor,
        'question': question,
        'sheets': sheets
    }
    return render(request, 'administration/practice/edit_question.html', parameters)


# ======================================== QUESTION REQUESTS ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def question_requests(request):
        
    instructor = Instructor.objects.get(id=request.user.id)
    
    questions = Question.objects.filter(is_approved=False)
    
    parameters = {
        'instructor': instructor,
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
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def test_cases(request, slug):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    question = Question.objects.get(slug=slug)
    
    test_cases = TestCase.objects.filter(question=question)
    
    parameters = {
        'instructor': instructor,
        'question': question,
        'test_cases': test_cases
    }
    return render(request, 'administration/practice/test_cases.html', parameters)


# ======================================== ADD TEST CASE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_test_case(request, slug):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    question = Question.objects.get(slug=slug)
    
    if request.method == 'POST':
        
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
        
        messages.success(request, 'Test case added successfully. Add More Test Cases')
        return redirect('add_test_case', slug=slug)
    
    parameters = {
        'instructor': instructor,
        'question': question
    }
    
    return render(request, 'administration/practice/add_test_case.html', parameters)


# ======================================== EDIT TEST CASE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_test_case(request, id):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    test_case = TestCase.objects.get(id=id)
    
    if request.method == 'POST':
        
        input_data = request.POST.get('input_data')
        expected_output = request.POST.get('expected_output')
        is_sample = 'is_sample' in request.POST  # Check if the checkbox is checked
        
        test_case.input_data = input_data
        test_case.expected_output = expected_output
        test_case.is_sample = is_sample

        test_case.save()
        
        messages.success(request, 'Test case updated successfully')
        return redirect('test_cases', slug=test_case.question.slug)
    
    parameters = {
        'instructor': instructor,
        'test_case': test_case
    }
    
    return render(request, 'administration/practice/edit_test_case.html', parameters)

# ======================================== DELETE TEST CASE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_test_case(request, id):
    
    test_case = TestCase.objects.get(id=id)
    
    test_case.delete()
    
    messages.success(request, 'Test case deleted successfully')
    return redirect('test_cases', slug=test_case.question.slug)


# ================================================================================================
# ============================================ POD WORK ==========================================
# ================================================================================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def instructor_pod(request):
    instructor = Instructor.objects.get(id=request.user.id)
    
    pods = POD.objects.filter(date__lte=datetime.date.today()).order_by('-date')
    
    parameters = {
        "instructor": instructor,
        "pods": pods
    }

    return render(request, "administration/practice/instructor_pod.html", parameters)


# =========================================== SET POD PAGE ================================


@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def set_pod(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    questions = Question.objects.filter(pods__isnull=True)
    
    parameters = {
        "instructor": instructor,
        "questions": questions
    }

    return render(request, 'administration/practice/set_pod.html', parameters)


# ================================================ SAVE POD ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
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
