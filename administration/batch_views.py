from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from accounts.models import Student, Administrator
from practice.models import POD, Submission, Question, Sheet, Batch,EnrollmentRequest
from django.db.models import Subquery, OuterRef
from angaar_hai.custom_decorators import admin_required


import datetime

# ========================= BATCH WORK ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def batches(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    batches = Batch.objects.all()
    
    parameters = {
        "administrator": administrator,
        "batches": batches
        
    }
    
    return render(request, 'administration/batch/batches.html', parameters)


# =================================== ADD BATCH ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def add_batch(request):
    
    administrator = Administrator.objects.get(id=request.user.id)

    
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        thumbnail = request.FILES.get('thumbnail')
        
        batch = Batch.objects.create(
            name=name,
            description=description,
            thumbnail=thumbnail
        )
        
        batch.save()
        
        messages.success(request, "Course added successfully")
        return redirect('administrator_batches')
        
    parameters = {
        "administrator": administrator
    }
    
    return render(request, 'administration/batch/add_batch.html', parameters)


# =============================== ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def enrollment_requests(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    total_pending_requests = EnrollmentRequest.objects.filter(status="Pending").count()
    
    parameters = {
        "administrator": administrator,
        "total_pending_requests": total_pending_requests
    }
    
    return render(request, "administration/batch/students_enroll_request.html", parameters)

# ================================ APPROVE ALL ENROLLMENT REQUESTS ====================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def approve_all_enrollments(request):
    enrollment_requests = EnrollmentRequest.objects.filter(status="Pending")
    for request in enrollment_requests:
        request.status = "Accepted"
        request.save()
        
    messages.success(request, "All pending enrollment requests have been accepted.")
    return redirect('administrator_enrollment_requests')

# =============================== FETCH PENDING ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def fetch_pending_enrollments(request):

    enrollment_requests = EnrollmentRequest.objects.select_related('student', 'batch').filter(status="Pending").order_by('-request_date')

        # Format the data for JSON response
    data = []
    for request_obj in enrollment_requests:
        data.append({
            'id': request_obj.id,
            'student_name': request_obj.student.first_name + " " + request_obj.student.last_name,
            'batch_name': request_obj.batch.name,
            'status': request_obj.status,
            "status_color": "success" if request_obj.status == "Accepted" else "danger",
            'request_date': request_obj.request_date.strftime('%d %b, %Y'),
        })

    # Return the data as a JSON response
    return JsonResponse({'success': True, 'data': data}, status=200)


# ================================== FETCH REJECTED ENROLLMENT REQUESTS ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def fetch_rejected_enrollments(request):
    
    enrollment_requests = EnrollmentRequest.objects.select_related('student', 'batch').filter(status="Rejected").order_by('-request_date')

    # Format the data for JSON response
    data = []
    for request_obj in enrollment_requests:
        data.append({
            'id': request_obj.id,
            'student_name': request_obj.student.first_name + request_obj.student.last_name,
            'batch_name': request_obj.batch.name,
            'status': request_obj.status,
            "status_color": "success" if request_obj.status == "Accepted" else "danger",
            'request_date': request_obj.request_date.strftime('%d %b, %Y'),
        })

    # Return the data as a JSON response
    return JsonResponse({'success': True, 'data': data}, status=200)

# =============================== ACCEPT ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def approve_enrollment(request, id):
    
    enrollment_request = EnrollmentRequest.objects.get(id=id)
    enrollment_request.status = "Accepted"
    enrollment_request.save()
    
    messages.success(request, "Enrollment request accepted")
    return redirect('administrator_enrollment_requests')

# =============================== REJECT ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def reject_enrollment(request, id):
    
    enrollment_request = EnrollmentRequest.objects.get(id=id)
    enrollment_request.status = "Rejected"
    enrollment_request.save()
    
    messages.success(request, "Enrollment request rejected")
    return redirect('administrator_enrollment_requests')


# =============================== BATCH DETAILS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def batch(request, slug):
    
    administrator = Administrator.objects.get(id=request.user.id)
    batch = Batch.objects.get(slug=slug)
    
    # Fetch all the sheets for this batch
    sheets = batch.sheets.all().order_by("-id")
        
    try:
        pod = POD.objects.get(batch=batch, date=datetime.date.today())
    except POD.DoesNotExist:
        pod = None
    

    parameters = {
        "administrator": administrator,
        "batch": batch,
        "sheets": sheets,
        "pod": pod
    }
    
    return render(request, 'administration/batch/batch.html', parameters)

# =============================== SET POD FOR BATCH ==============================



def fetch_questions(request):
    query = request.GET.get("query", "")
    
    questions = Question.objects.filter(
        Q(title__icontains=query), 
        pods__batch__isnull=True,
        is_approved=True, 
        parent_id=-1
    ).distinct()
    
    
    question_list = [{"id": q.id, "title": q.title} for q in questions]
    return JsonResponse({"questions": question_list})


@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def administrator_set_pod_for_batch(request, slug):
    batch = get_object_or_404(Batch, slug=slug)

    # Fetch existing PODs for the batch
    
    pods = POD.objects.select_related('question').filter(batch=batch)
    
    today_pod = pods.filter(date=datetime.datetime.today().date())
    past_pods = pods.order_by('-date').exclude(date__gt=datetime.datetime.today().date())
    upcoming_pods = pods.filter(date__gt=datetime.datetime.today().date()).order_by('date')

    parameters = {
        "batch": batch,
        "pod": today_pod,
        "past_pods": past_pods,
        "upcoming_pods": upcoming_pods,
        "default_date": now().date().isoformat(),  # Set default date for the form
    }

    return render(request, 'administration/batch/set_pod.html', parameters)


@csrf_exempt
def set_pod(request, slug):
    if request.method == "POST":
        question_id = request.POST.get("question_id")
        pod_date = request.POST.get("pod_date")
        batch = get_object_or_404(Batch, slug=slug)

        if question_id and pod_date:
            try:
                pod_date = datetime.datetime.strptime(pod_date, "%Y-%m-%d").date()
                if pod_date < now().date():
                    return JsonResponse({"success": False, "message": "Cannot set a POD for a past date."})

                question = get_object_or_404(Question, id=question_id)
                if POD.objects.filter(batch=batch, date=pod_date).exists():
                    return JsonResponse({"success": False, "message": "POD already exists for the selected date."})

                POD.objects.create(question=question, batch=batch, date=pod_date)
                return JsonResponse({"success": True, "message": "POD set successfully!"})
            except ValueError:
                return JsonResponse({"success": False, "message": "Invalid date format."})

        return JsonResponse({"success": False, "message": "Please select a valid question and date."})


# =============================== VIEW SUBMISSIONS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def view_submissions(request, slug):
    question = get_object_or_404(Question, slug=slug)
    administrator = Administrator.objects.get(id=request.user.id)
    
    parameters = {
        "question": question,
        "administrator": administrator
    }
    
    return render(request, 'administration/batch/view_submissions.html', parameters)


# ================================= BATCH ENROLLMENT REQUESTS ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def batch_enrollment_requests(request, slug):
    
    administrator = Administrator.objects.get(id=request.user.id)
    batch = Batch.objects.get(slug=slug)
    total_pending_requests = EnrollmentRequest.objects.filter(batch=batch, status="Pending").count()
    
    parameters = {
        "administrator": administrator,
        "batch": batch,
        "total_pending_requests": total_pending_requests
    }
    
    return render(request, "administration/batch/batch_enrollment_requests.html", parameters)

# =============================== FETCH PENDING ENROLLMENT REQUESTS OF BATCH ===================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def fetch_pending_enrollments_of_batch(request, slug):
    
    batch = Batch.objects.get(slug=slug)
    enrollment_requests = EnrollmentRequest.objects.select_related('student', 'batch').filter(batch=batch, status="Pending").order_by('-request_date')

    # Format the data for JSON response
    data = []
    for request_obj in enrollment_requests:
        data.append({
            'id': request_obj.id,
            'student_name': request_obj.student.first_name + " " + request_obj.student.last_name,
            'status': request_obj.status,
            "status_color": "success" if request_obj.status == "Accepted" else "danger",
            'request_date': request_obj.request_date.strftime('%d %b, %Y'),
        })

    # Return the data as a JSON response
    return JsonResponse({'success': True, 'data': data}, status=200)

# =============================== FETCH REJECTED ENROLLMENT REQUESTS OF BATCH ===================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def fetch_rejected_enrollments_of_batch(request, slug):
    
    batch = Batch.objects.get(slug=slug)
    enrollment_requests = EnrollmentRequest.objects.select_related('student', 'batch').filter(batch=batch, status="Rejected").order_by('-request_date')

    # Format the data for JSON response
    data = []
    for request_obj in enrollment_requests:
        data.append({
            'id': request_obj.id,
            'student_name': request_obj.student.first_name + " " + request_obj.student.last_name,
            'status': request_obj.status,
            "status_color": "success" if request_obj.status == "Accepted" else "danger",
            'request_date': request_obj.request_date.strftime('%d %b, %Y'),
        })

    # Return the data as a JSON response
    return JsonResponse({'success': True, 'data': data}, status=200)

# =============================== ACCEPT ENROLLMENT REQUESTS OF BATCH ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def approve_enrollment_batch(request, id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # Check if the request is AJAX
        try:
            enrollment_request = EnrollmentRequest.objects.get(id=id)
            enrollment_request.status = "Accepted"
            enrollment_request.save()
            return JsonResponse({
                'success': True,
                'message': 'Enrollment request accepted',
                'id': id
            })
        except EnrollmentRequest.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Enrollment request not found'
            }, status=404)
    else:
        messages.success(request, "Enrollment request accepted")
        return redirect('administrator_batch_enrollment_requests', slug=enrollment_request.batch.slug)


# =============================== REJECT ENROLLMENT REQUESTS OF BATCH ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def reject_enrollment_batch(request, id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            enrollment_request = EnrollmentRequest.objects.get(id=id)
            enrollment_request.status = "Rejected"
            enrollment_request.save()
            return JsonResponse({
                'success': True,
                'message': 'Enrollment request rejected',
                'id': id
            })
        except EnrollmentRequest.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Enrollment request not found'
            }, status=404)
    else:
        messages.success(request, "Enrollment request rejected")
        return redirect('administrator_batch_enrollment_requests', slug=enrollment_request.batch.slug)
    
# ================================ APPROVE ALL ENROLLMENT BATCH ====================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def approve_all_enrollments_batch(request, id):
    batch = Batch.objects.get(id=id)
    enrollment_requests = EnrollmentRequest.objects.filter(batch = batch, status="Pending")
    for req in enrollment_requests:
        req.status = "Accepted"
        req.save()
        
    messages.success(request, "All pending enrollment requests have been accepted.")
    return redirect('administrator_batch_enrollment_requests', slug=batch.slug)


# ======================================================== LEADERBOARD =====================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def leaderboard(request, slug):

    batch = Batch.objects.get(slug=slug)
    
    parameters = {
        "batch": batch,
    }
    
    return render(request, 'administration/batch/leaderboard.html', parameters)


# ==================================== FETCH LEADERBOARD ======================

from django.db.models import Count, Min, Max    
def fetch_batch_leaderboard(request, slug):
        
    batch = get_object_or_404(Batch, slug=slug)
    sheets = batch.sheets.all()
    total_questions = Question.objects.filter(sheets__in=sheets).distinct()

    # Aggregate submission data at the database level
    submissions = Submission.objects.filter(
        question__in=total_questions,
        status='Accepted'
    ).values(
        'user_id', 'question_id', 'question__sheets__id'
    ).annotate(
        max_score=Max('score'),
        earliest_submission=Min('submitted_at')
    )

    # Process aggregated data
    user_scores = {}
    for sub in submissions:
        user_id = sub['user_id']
        question_id = sub['question_id']
        sheet_id = sub['question__sheets__id']

        if user_id not in user_scores:
            user_scores[user_id] = {
                'total_score': 0,
                'earliest_submission': sub['earliest_submission'],
                'solved_questions': set(),
                'sheet_breakdown': {}
            }

        # Add score
        user_scores[user_id]['total_score'] += sub['max_score']
        user_scores[user_id]['earliest_submission'] = min(
            user_scores[user_id]['earliest_submission'], sub['earliest_submission']
        )
        user_scores[user_id]['solved_questions'].add(question_id)

        # Sheet breakdown
        if sheet_id not in user_scores[user_id]['sheet_breakdown']:
            user_scores[user_id]['sheet_breakdown'][sheet_id] = 0
        user_scores[user_id]['sheet_breakdown'][sheet_id] += 1

    # Format leaderboard
    leaderboard = []
    solved_question_counts = {}

    for user_id, data in user_scores.items():
        user = Student.objects.get(id=user_id)
        solved_problems = len(data['solved_questions'])

        # Map sheet IDs to sheet names
        sheet_details = {
            Sheet.objects.get(id=sheet_id).name: count
            for sheet_id, count in data['sheet_breakdown'].items()
        }

        leaderboard.append({
            'student': {
                'id': user_id,
                'name': f"{user.first_name} {user.last_name}",
            },
            'total_score': data['total_score'],
            'earliest_submission': data['earliest_submission'],
            'solved_problems': solved_problems,
            'sheet_breakdown': sheet_details,
        })

        if solved_problems not in solved_question_counts:
            solved_question_counts[solved_problems] = 0
        solved_question_counts[solved_problems] += 1

    # Sort leaderboard by total score and earliest submission
    leaderboard.sort(key=lambda x: (-x['total_score'], x['earliest_submission']))
    

    return JsonResponse({
        'leaderboard': leaderboard,
        'solved_question_counts': solved_question_counts
    })
