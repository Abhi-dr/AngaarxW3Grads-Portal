from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from practice.models import Sheet
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.db.models import OuterRef, Subquery


from practice.models import Question, Submission

# ================================== FETCH ALL SHEETS ==================================

def fetch_all_sheets(request):   
    
    cached_data = cache.get('fetch_all_sheets')
    if cached_data:
        return JsonResponse({'data': cached_data})
    
    sheets = Sheet.objects.filter(is_approved=True).prefetch_related('batches', 'questions').order_by('-id')

    data = [
        {
            "id": sheet.id,
            "name": sheet.name,
            "slug": sheet.slug,
            "thumbnail": sheet.thumbnail.url,
            "batches": ", ".join([batch.name for batch in sheet.batches.all()]),
            "questions": sheet.questions.count(),
            "is_enabled": sheet.is_enabled,
            "is_sequential": sheet.is_sequential,
            "is_approved": sheet.is_approved,
        } for sheet in sheets
    ]
    
     # Store data in cache
    cache.set('fetch_all_sheets', data, timeout=900)  # Cache for 15 minutes

    return JsonResponse({'data': data})

# ================================================ VIEW SUBMISSION API =================================


def fetch_question_submissions(request, slug):
    question = get_object_or_404(Question, slug=slug)
    
    latest_submission_time = Submission.objects.filter(
        question=question, 
        user=OuterRef('user'), 
        status="Accepted"
    ).select_related('user').order_by('-submitted_at').values('submitted_at')[:1]

    latest_submissions = Submission.objects.filter(
        question=question, 
        status="Accepted", 
        submitted_at=Subquery(latest_submission_time)
    ).select_related('user').order_by('-submitted_at')

    submissions_data = [
        {
            "id": submission.id,
            "user": f"{submission.user.first_name} {submission.user.last_name}",
            "status": submission.status,
            "submitted_at": submission.submitted_at,
            "code": submission.code,
        }
        for submission in latest_submissions
    ]
    
    return JsonResponse({"submissions": submissions_data})
