from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from home.models import FlamesCourse, FlamesRegistration, FlamesCourseTestimonial
from accounts.models import Instructor

@login_required
def flames_courses(request):
    """
    Admin view for managing FLAMES courses
    """
    courses = FlamesCourse.objects.all()
    
    # Count stats
    total_courses = courses.count()
    active_courses = courses.filter(is_active=True).count()
    total_registrations = FlamesRegistration.objects.count()
    
    context = {
        'courses': courses,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'total_registrations': total_registrations,
    }
    
    return render(request, 'administration/flames/courses.html', context)

@login_required
def flames_registrations(request):
    """
    Admin view for managing FLAMES registrations with filtering capability
    """
    registrations = FlamesRegistration.objects.all().select_related('course')
    courses = FlamesCourse.objects.all()
    
    # Get stats for dashboard
    total_registrations = registrations.count()
    pending_registrations = registrations.filter(status="Pending").count()
    approved_registrations = registrations.filter(status="Approved").count()
    
    # Get unique colleges for filter
    colleges = registrations.values_list('college', flat=True).distinct()
    
    context = {
        'registrations': registrations,
        'courses': courses,
        'colleges': colleges,
        'total_registrations': total_registrations,
        'pending_registrations': pending_registrations,
        'approved_registrations': approved_registrations,
    }
    
    return render(request, 'administration/flames/registrations.html', context)

@login_required
def admin_course_detail(request, course_id):
    """
    View a specific course details in admin panel
    """
    course = get_object_or_404(FlamesCourse, id=course_id)
    registrations = FlamesRegistration.objects.filter(course=course)
    testimonials = FlamesCourseTestimonial.objects.filter(course=course)
    
    context = {
        'course': course,
        'registrations': registrations,
        'testimonials': testimonials,
        'registration_count': registrations.count(),
    }
    
    return render(request, 'administration/flames/course_detail.html', context)

@login_required
def admin_add_course(request):
    """
    Add a new FLAMES course
    """
    if request.method == 'POST':
        # Extract form data
        title = request.POST.get('title')
        subtitle = request.POST.get('subtitle')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        what_you_will_learn = request.POST.get('what_you_will_learn')
        roadmap = request.POST.get('roadmap')
        icon_class = request.POST.get('icon_class')
        icon_color = request.POST.get('color')
        button_color = request.POST.get('button_color')
        instructor_name = request.POST.get('instructor')
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price') or None
        is_active = 'is_active' in request.POST
        
        
        # Create course
        course = FlamesCourse.objects.create(
            title=title,
            subtitle=subtitle,
            slug=slug,
            description=description,
            what_you_will_learn=what_you_will_learn,
            roadmap=roadmap,
            icon_class=icon_class,
            icon_color=icon_color,
            button_color=button_color,
            instructor=instructor_name,
            price=price,
            discount_price=discount_price,
            is_active=is_active
        )
        
        return redirect('admin_flames_courses')
    
    # Get all instructors to display in the form
    instructors = Instructor.objects.all()
    context = {
        'instructors': instructors
    }
    
    return render(request, 'administration/flames/courses.html', context)

@login_required
def admin_edit_course(request, course_id):
    """
    Edit an existing FLAMES course
    """
    course = get_object_or_404(FlamesCourse, id=course_id)
    
    if request.method == 'POST':
        # Extract form data
        course.title = request.POST.get('title')
        course.subtitle = request.POST.get('subtitle')
        course.slug = request.POST.get('slug')
        course.description = request.POST.get('description')
        course.what_you_will_learn = request.POST.get('what_you_will_learn')
        course.roadmap = request.POST.get('roadmap')
        course.icon_class = request.POST.get('icon_class')
        course.icon_color = request.POST.get('color')
        course.button_color = request.POST.get('button_color')
        course.instructor = request.POST.get('instructor')
        course.price = request.POST.get('price')
        course.discount_price = request.POST.get('discount_price') or None
        course.is_active = 'is_active' in request.POST
        course.save()
        
        return redirect('admin_course_detail', course_id=course.id)
    
    # Get all instructors to display in the form
    instructors = Instructor.objects.all()
    
    context = {
        'course': course,
        'instructors': instructors
    }
    
    return render(request, 'administration/flames/edit_course.html', context)

@login_required
@require_POST
def admin_toggle_course_status(request):
    """
    Toggle a course's active status
    """
    course_id = request.POST.get('course_id')
    is_active = request.POST.get('is_active') == 'true'
    
    try:
        course = get_object_or_404(FlamesCourse, id=course_id)
        course.is_active = is_active
        course.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Course status updated to {"active" if is_active else "inactive"}'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def admin_registrations_ajax(request):
    """
    AJAX endpoint for getting filtered registrations data
    """
    
    # Extract filter parameters
    course_id = request.GET.get('course', '')
    status = request.GET.get('status', '')
    year = request.GET.get('year', '')
    college = request.GET.get('college', '')
    search = request.GET.get('search', '')
    
    # Start with all registrations
    registrations = FlamesRegistration.objects.all().select_related('course')
    
    # Apply filters
    if course_id:
        registrations = registrations.filter(course_id=course_id)
    
    if status:
        # Handle case-insensitive status filtering
        if status.lower() == 'pending':
            registrations = registrations.filter(status='Pending')
        elif status.lower() == 'approved':
            registrations = registrations.filter(status='Approved')
        elif status.lower() == 'rejected':
            registrations = registrations.filter(status='Rejected')
        elif status.lower() == 'completed':
            registrations = registrations.filter(status='Completed')
    
    if year:
        registrations = registrations.filter(year=year)
    
    if college:
        registrations = registrations.filter(college=college)
    
    if search:
        registrations = registrations.filter(
            Q(full_name__icontains=search) | 
            Q(email__icontains=search) | 
            Q(contact_number__icontains=search) |
            Q(college__icontains=search)
        )
    
    # Prepare data for DataTables
    data = []
    for reg in registrations:
        data.append({
            'id': reg.id,
            'full_name': reg.full_name,
            'course': {
                'title': reg.course.title,
                'color': reg.course.icon_color
            },
            'email': reg.email,
            'contact_number': reg.contact_number,
            'college': reg.college,
            'year': reg.year,
            'created_at': reg.created_at.strftime('%d %b %Y, %I:%M %p'),
            'status': reg.status
        })
    # Make sure to return in the format DataTables expects
    return JsonResponse({
        'data': data,
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': FlamesRegistration.objects.count(),
        'recordsFiltered': len(data)
    })

@login_required
def admin_registration_details(request):
    """
    Get registration details for modal view
    """
    reg_id = request.GET.get('id')
    
    try:
        registration = get_object_or_404(FlamesRegistration, id=reg_id)
        
        data = {
            'id': registration.id,
            'name': registration.full_name,
            'email': registration.email,
            'phone': registration.contact_number,
            'course': registration.course.title,
            'college': registration.college,
            'year': registration.year,
            'message': registration.message or '',
            'status': registration.status,
            'payment_id': registration.payment_id or '',
            'admin_notes': registration.admin_notes or '',
            'created_at': registration.created_at.strftime('%d %b %Y, %I:%M %p'),
            'updated_at': registration.updated_at.strftime('%d %b %Y, %I:%M %p') if registration.updated_at else '',
        }
        
        return JsonResponse({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def admin_update_registration_status(request):
    """
    Update a registration's status
    """
    reg_id = request.POST.get('id')
    status = request.POST.get('status').capitalize()
    
    try:
        registration = get_object_or_404(FlamesRegistration, id=reg_id)
        registration.status = status
        registration.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Registration status updated to {status}'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def admin_update_registration_notes(request):
    """
    Update admin notes for a registration
    """
    reg_id = request.POST.get('id')
    notes = request.POST.get('notes')
    
    try:
        registration = get_object_or_404(FlamesRegistration, id=reg_id)
        registration.admin_notes = notes
        registration.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Notes updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def admin_add_testimonial(request):
    """
    Add a testimonial for a course
    """
    course_id = request.POST.get('course_id')
    student_name = request.POST.get('student_name')
    rating = request.POST.get('rating')
    content = request.POST.get('content')
    
    try:
        course = get_object_or_404(FlamesCourse, id=course_id)
        
        testimonial = FlamesCourseTestimonial.objects.create(
            course=course,
            student_name=student_name,
            rating=rating,
            content=content
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Testimonial added successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }) 