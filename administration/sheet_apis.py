from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from practice.models import Sheet
from django.core.cache import cache

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
            "is_approved": sheet.is_approved
        } for sheet in sheets
    ]
    
     # Store data in cache
    cache.set('fetch_all_sheets', data, timeout=900)  # Cache for 15 minutes

    return JsonResponse({'data': data})

