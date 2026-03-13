from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
import json
from django.utils import timezone
import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from administration.models import Achievement
from accounts.models import CustomUser
from django.db.models import Q


DEFAULT_PROFILE_PIC_URL = '/static/img/student/default-avatar.svg'


def get_student_profile_pic_url(student):
    profile_pic = getattr(student, 'profile_pic', None)
    if not profile_pic:
        return DEFAULT_PROFILE_PIC_URL

    profile_pic_name = (getattr(profile_pic, 'name', '') or '').lstrip('/')
    if not profile_pic_name or profile_pic_name == 'student_profile/default.jpg':
        return DEFAULT_PROFILE_PIC_URL

    try:
        if hasattr(profile_pic, 'storage') and not profile_pic.storage.exists(profile_pic_name):
            return DEFAULT_PROFILE_PIC_URL
    except Exception:
        return DEFAULT_PROFILE_PIC_URL

    try:
        return profile_pic.url
    except Exception:
        return DEFAULT_PROFILE_PIC_URL

# =================================== ALL ACHIEVEMENTS ===============================

@staff_member_required
def achievements_view(request):
    """Render the achievements management page."""
    return render(request, 'administration/achievements.html')

@staff_member_required
@require_http_methods(["GET"])
def get_achievements(request):
    """API to fetch all achievements with pagination."""
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        search_query = request.GET.get('search', '').strip()
        
        achievements = Achievement.objects.select_related('student').order_by('-date')
        
        if search_query:
            achievements = achievements.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(student__username__icontains=search_query)
            )
        
        paginator = Paginator(achievements, per_page)
        current_page = paginator.get_page(page)
        
        data = {
            'achievements': [{
                'id': achievement.id,
                'student': {
                    'id': achievement.student.id,
                    'username': achievement.student.username,
                    'name': achievement.student.first_name + ' ' + achievement.student.last_name,
                    'profile_pic': get_student_profile_pic_url(achievement.student)
                },
                'title': achievement.title,
                'description': achievement.description,
                'achievement_type': achievement.achievement_type,
                'date': achievement.date.strftime('%Y-%m-%d')
            } for achievement in current_page],
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_count': paginator.count
        }
        
        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@staff_member_required
@require_http_methods(["GET"])
def get_achievement(request, achievement_id):
    """API to fetch a single achievement."""
    try:
        achievement = get_object_or_404(Achievement, id=achievement_id)
        data = {
            'id': achievement.id,
            'student': {
                'id': achievement.student.id,
                'name': (achievement.student.first_name + ' ' + achievement.student.last_name).strip() or achievement.student.username,
                'username': achievement.student.username,
                'profile_pic': get_student_profile_pic_url(achievement.student)
            },
            'title': achievement.title,
            'description': achievement.description,
            'achievement_type': achievement.achievement_type,
            'date': achievement.date.strftime('%Y-%m-%d')
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@staff_member_required
@require_http_methods(["POST"])
def create_achievement(request):
    """API to create a new achievement."""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['student_id', 'title', 'description', 'achievement_type', 'date']
        if not all(field in data for field in required_fields):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required fields'
            }, status=400)
            
        student = get_object_or_404(CustomUser, id=data['student_id'])
        
        achievement = Achievement.objects.create(
            student=student,
            title=data['title'],
            description=data['description'],
            achievement_type=data['achievement_type'],
            date=datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
        )
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'id': achievement.id,
                'student': {
                    'id': student.id,
                    'username': student.username,
                    'profile_pic': get_student_profile_pic_url(student)
                },
                'title': achievement.title,
                'description': achievement.description,
                'achievement_type': achievement.achievement_type,
                'date': achievement.date.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@staff_member_required
@require_http_methods(["PUT"])
def update_achievement(request, achievement_id):
    """API to update an existing achievement."""
    try:
        achievement = get_object_or_404(Achievement, id=achievement_id)
        data = json.loads(request.body)
        
        # Update fields if provided
        if 'title' in data:
            achievement.title = data['title']
        if 'description' in data:
            achievement.description = data['description']
        if 'achievement_type' in data:
            achievement.achievement_type = data['achievement_type']
        if 'date' in data:
            achievement.date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'student_id' in data:
            student = get_object_or_404(CustomUser, id=data['student_id'])
            achievement.student = student
            
        achievement.save()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'id': achievement.id,
                'student': {
                    'id': achievement.student.id,
                    'username': achievement.student.username,
                    'profile_pic': get_student_profile_pic_url(achievement.student)
                },
                'title': achievement.title,
                'description': achievement.description,
                'achievement_type': achievement.achievement_type,
                'date': achievement.date.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@staff_member_required
@require_http_methods(["DELETE"])
def delete_achievement(request, achievement_id):
    """API to delete an achievement."""
    try:
        achievement = get_object_or_404(Achievement, id=achievement_id)
        achievement.delete()
        return JsonResponse({'status': 'success', 'message': 'Achievement deleted successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
