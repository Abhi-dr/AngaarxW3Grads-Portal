from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import HttpResponse
from django.utils.timezone import now
from django.utils.timezone import make_naive
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from datetime import timedelta
from django.core.paginator import Paginator
from django.db.models import Min, Max

from accounts.models import CustomUser
from student.models import Notification
from practice.models import POD, Submission, Question, Sheet, Batch,EnrollmentRequest
from django.db.models import Subquery, OuterRef
from angaar_hai.custom_decorators import admin_required


import datetime
import json
import pandas as pd

# ========================= INSTRUCTOR BATCH WORK ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def batches(request):
    batches = Batch.objects.order_by("-id")

    parameters = {
        "batches": batches,
    }

    return render(request, 'instructor/batch/batches.html', parameters)


@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_batch_request(request):
    if request.method == "POST":
        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        thumbnail = request.FILES.get('thumbnail')

        if not name:
            messages.error(request, "Course name is required.")
            return render(request, 'instructor/batch/add_batch_request.html')

        if Batch.objects.filter(name__iexact=name).exists():
            messages.error(request, "A course with this name already exists.")
            return render(request, 'instructor/batch/add_batch_request.html')

        batch = Batch.objects.create(
            name=name,
            description=description,
            thumbnail=thumbnail,
            is_active=False,
        )

        reviewer_url = reverse('administrator_batches')
        requester = request.user.get_full_name() or request.user.email
        Notification.objects.create(
            title='Approval Request: Course',
            description=f"{requester} created Course '{batch.name}' and requested admin approval. Review: {reviewer_url}",
            is_alert=True,
            is_fixed=False,
            type='warning',
            expiration_date=now() + timedelta(days=30),
        )

        messages.success(request, "Course request sent to admin for approval.")
        return redirect('instructor_batches')

    return redirect('instructor_batches')


# =============================== BATCH DETAILS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def batch(request, slug):
    
    batch = Batch.objects.get(slug=slug)
    
    # Fetch all the sheets for this batch
    sheets = batch.sheets.all().order_by("-id")
        
    try:
        pod = POD.objects.get(batch=batch, date=datetime.date.today())
    except POD.DoesNotExist:
        pod = None
    

    parameters = {
        "batch": batch,
        "sheets": sheets,
        "pod": pod
    }
    
    return render(request, 'instructor/batch/batch.html', parameters)


@login_required(login_url='login')
@staff_member_required(login_url='login')
def bulk_update_batch_sheets(request, slug):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    batch = get_object_or_404(Batch, slug=slug)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        payload = {}

    action = payload.get('action')
    sheets_qs = batch.sheets.all()

    if action == 'enable_all':
        count = sheets_qs.update(is_enabled=True)
        return JsonResponse({'success': True, 'message': f'Enabled {count} sheet(s).'})

    if action == 'approve_all':
        count = sheets_qs.update(is_approved=True)
        return JsonResponse({'success': True, 'message': f'Approved {count} sheet(s).'})

    return JsonResponse({'success': False, 'error': 'Invalid action.'}, status=400)


@login_required(login_url='login')
@staff_member_required(login_url='login')
def update_batch(request, slug):
    if request.method not in ['POST', 'PATCH']:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    batch = get_object_or_404(Batch, slug=slug)

    name = (request.POST.get('name') or '').strip()
    description = (request.POST.get('description') or '').strip()
    is_active = str(request.POST.get('is_active', '')).lower() in ['1', 'true', 'on', 'yes']
    thumbnail = request.FILES.get('thumbnail')

    if not name:
        return JsonResponse({'success': False, 'error': 'Course name is required.'}, status=400)

    if Batch.objects.exclude(id=batch.id).filter(name__iexact=name).exists():
        return JsonResponse({'success': False, 'error': 'Another course with this name already exists.'}, status=400)

    batch.name = name
    batch.description = description
    batch.is_active = is_active
    if thumbnail:
        batch.thumbnail = thumbnail
    batch.save()

    return JsonResponse({
        'success': True,
        'message': 'Course updated successfully.',
        'data': {
            'name': batch.name,
            'description': batch.description or '',
            'is_active': batch.is_active,
            'thumbnail': batch.thumbnail.url if batch.thumbnail else None,
        }
    })


@login_required(login_url='login')
@staff_member_required(login_url='login')
def toggle_batch_active(request, slug):
    if request.method not in ['POST', 'PATCH']:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    batch = get_object_or_404(Batch, slug=slug)
    batch.is_active = not batch.is_active
    batch.save(update_fields=['is_active'])

    return JsonResponse({
        'success': True,
        'is_active': batch.is_active,
        'message': f"Course {'activated' if batch.is_active else 'deactivated'} successfully.",
    })


@login_required(login_url='login')
@staff_member_required(login_url='login')
def batch_sheet(request, batch_slug, sheet_slug):
    batch = get_object_or_404(Batch, slug=batch_slug)
    sheet = get_object_or_404(Sheet, slug=sheet_slug, batches=batch)
    questions = sheet.get_ordered_questions()

    parameters = {
        "batch": batch,
        "sheet": sheet,
        "questions": questions,
        "from_course": True,
        "course_slug": batch.slug,
        "return_url": request.path,
    }

    return render(request, 'instructor/sheet/sheet.html', parameters)


@login_required(login_url='login')
@staff_member_required(login_url='login')
def reorder_batch_sheets(request, slug):
    """Render drag-and-drop reorder page for instructor batch sheets."""
    batch = get_object_or_404(Batch, slug=slug)
    sheets = batch.get_ordered_sheets()
    parameters = {
        "batch": batch,
        "sheets": sheets,
    }
    return render(request, 'instructor/batch/reorder_sheets.html', parameters)


# =============================== SET POD FOR BATCH ==============================


@login_required(login_url='login')
@staff_member_required(login_url='login')
def set_pod_for_batch(request, slug):
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

    return render(request, 'instructor/batch/set_pod.html', parameters)

# =============================== VIEW SUBMISSIONS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def view_submissions(request, slug):
    question = get_object_or_404(Question, slug=slug)
    
    parameters = {
        "question": question,
    }
    
    return render(request, 'instructor/batch/view_submissions.html', parameters)

# ================================= BATCH ENROLLMENT REQUESTS ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def batch_enrollment_requests(request, slug):
    
    batch = Batch.objects.get(slug=slug)
    total_pending_requests = EnrollmentRequest.objects.filter(batch=batch, status="Pending").count()
    
    parameters = {
        "batch": batch,
        "total_pending_requests": total_pending_requests
    }
    
    return render(request, "instructor/batch/batch_enrollment_requests.html", parameters)


# ================================= BATCH LEADERBOARD ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def batch_leaderboard(request, slug):
    batch = get_object_or_404(Batch, slug=slug)
    return render(request, 'instructor/batch/leaderboard.html', {"batch": batch})


@login_required(login_url='login')
@staff_member_required(login_url='login')
def fetch_batch_leaderboard(request, slug):
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 10)), 100)

    batch = get_object_or_404(Batch, slug=slug)
    sheets = batch.sheets.all()
    total_questions = Question.objects.filter(sheets__in=sheets).distinct()

    submissions = Submission.objects.filter(
        question__in=total_questions,
        status='Accepted'
    ).values(
        'user_id', 'question_id', 'question__sheets__id'
    ).annotate(
        max_score=Max('score'),
        earliest_submission=Min('submitted_at')
    )

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

        user_scores[user_id]['total_score'] += sub['max_score']
        user_scores[user_id]['earliest_submission'] = min(
            user_scores[user_id]['earliest_submission'], sub['earliest_submission']
        )
        user_scores[user_id]['solved_questions'].add(question_id)

        if sheet_id not in user_scores[user_id]['sheet_breakdown']:
            user_scores[user_id]['sheet_breakdown'][sheet_id] = 0
        user_scores[user_id]['sheet_breakdown'][sheet_id] += 1

    leaderboard = []
    for user_id, data in user_scores.items():
        user = CustomUser.objects.get(id=user_id)
        solved_problems = len(data['solved_questions'])

        sheet_details = {
            Sheet.objects.get(id=sheet_id).name: count
            for sheet_id, count in data['sheet_breakdown'].items()
        }

        leaderboard.append({
            'student': {
                'id': user_id,
                'name': f"{user.first_name} {user.last_name}".strip() or user.email,
            },
            'total_score': data['total_score'],
            'earliest_submission': data['earliest_submission'],
            'solved_problems': solved_problems,
            'sheet_breakdown': sheet_details,
        })

    leaderboard.sort(key=lambda x: (-x['total_score'], x['earliest_submission']))

    paginator = Paginator(leaderboard, page_size)
    try:
        paginated_leaderboard = paginator.page(page)
    except Exception:
        paginated_leaderboard = paginator.page(paginator.num_pages if paginator.num_pages else 1)

    start_rank = (paginated_leaderboard.number - 1) * page_size + 1
    for idx, entry in enumerate(paginated_leaderboard.object_list):
        entry['rank'] = start_rank + idx

    return JsonResponse({
        'leaderboard': list(paginated_leaderboard.object_list),
        'pagination': {
            'current_page': paginated_leaderboard.number,
            'total_pages': paginator.num_pages,
            'page_size': page_size,
            'total_count': paginator.count,
            'has_next': paginated_leaderboard.has_next(),
            'has_previous': paginated_leaderboard.has_previous(),
        }
    })


@login_required(login_url='login')
@staff_member_required(login_url='login')
def download_batch_leaderboard_excel(request, slug):
    batch = get_object_or_404(Batch, slug=slug)
    sheets = batch.sheets.all()
    total_questions = Question.objects.filter(sheets__in=sheets).distinct()

    submissions = Submission.objects.filter(
        question__in=total_questions,
        status='Accepted'
    ).values(
        'user_id', 'question_id', 'question__sheets__id'
    ).annotate(
        max_score=Max('score'),
        earliest_submission=Min('submitted_at')
    )

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

        user_scores[user_id]['total_score'] += sub['max_score']
        user_scores[user_id]['earliest_submission'] = min(
            user_scores[user_id]['earliest_submission'], sub['earliest_submission']
        )
        user_scores[user_id]['solved_questions'].add(question_id)

        if sheet_id not in user_scores[user_id]['sheet_breakdown']:
            user_scores[user_id]['sheet_breakdown'][sheet_id] = 0
        user_scores[user_id]['sheet_breakdown'][sheet_id] += 1

    leaderboard = []
    for user_id, data in user_scores.items():
        user = CustomUser.objects.get(id=user_id)
        solved_problems = len(data['solved_questions'])

        sheet_details = {
            Sheet.objects.get(id=sheet_id).name: count
            for sheet_id, count in data['sheet_breakdown'].items()
        }

        leaderboard.append({
            'Student ID': user_id,
            'Student Name': f"{user.first_name} {user.last_name}".strip() or user.email,
            'Total Score': data['total_score'],
            'Earliest Submission': make_naive(data['earliest_submission']) if data['earliest_submission'] else None,
            'Solved Problems': solved_problems,
            'Sheet Breakdown': '; '.join([f"{sheet}: {count}" for sheet, count in sheet_details.items()])
        })

    leaderboard.sort(key=lambda x: (-x['Total Score'], x['Earliest Submission'] or datetime.datetime.max))
    for idx, entry in enumerate(leaderboard):
        entry['Rank'] = idx + 1

    export_columns = [
        'Rank',
        'Student ID',
        'Student Name',
        'Total Score',
        'Earliest Submission',
        'Solved Problems',
        'Sheet Breakdown',
    ]
    df = pd.DataFrame(leaderboard, columns=export_columns)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="batch_leaderboard_{slug}.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leaderboard')

    return response
