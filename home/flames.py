from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import FlamesCourse, FlamesCourseTestimonial, FlamesRegistration

# ===================================== FLAMES PAGE ==============================

def flames(request):
    courses = FlamesCourse.objects.filter(is_active=True)
    return render(request, "home/flames.html", {'courses': courses})

# =================================== PROGRAM DETAILS ============================

def course_detail(request, slug):
    course = get_object_or_404(FlamesCourse, slug=slug, is_active=True)
    testimonials = FlamesCourseTestimonial.objects.filter(course=course)
    
    context = {
        'course': course,
        'testimonials': testimonials,
        'learning_points': course.get_learning_points(),
    }
    
    return render(request, "home/course_detail.html", context)

# =================================== REGISTER COURSE ============================

def register_course(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        course_id = request.POST.get('course_id')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        contact_number = request.POST.get('contact_number')
        college = request.POST.get('college')
        year = request.POST.get('year')
        
        try:
            course = FlamesCourse.objects.get(id=course_id, is_active=True)
            registration = FlamesRegistration.objects.create(
                course=course,
                full_name=full_name,
                email=email,
                contact_number=contact_number,
                college=college,
                year=year
            )
            
            return JsonResponse({
                'status': 'success',
                'message': f'Successfully registered for {course.title}!'
            })
        except FlamesCourse.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Course not found or not active.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)
