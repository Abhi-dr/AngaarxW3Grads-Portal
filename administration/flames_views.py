from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from home.models import FlamesCourse, FlamesRegistration, FlamesCourseTestimonial, FlamesTeam, Alumni, FlamesTeamMember
from accounts.models import Instructor

@login_required
def flames_courses(request):
    """
    Admin view for managing FLAMES courses
    """
    courses = FlamesCourse.objects.all()
    
    # Count stats
    total_courses = courses.count()
    
    total_registrations = FlamesRegistration.objects.count()
    total_completed_registrations = FlamesRegistration.objects.filter(status="Completed").count()
    total_pending_registrations = FlamesRegistration.objects.filter(status="Pending").count()
    
    total_amount = FlamesRegistration.get_total_amount()
    
    context = {
        'courses': courses,
        'total_courses': total_courses,
        
        'total_registrations': total_registrations,
        'total_completed_registrations': total_completed_registrations,
        'total_pending_registrations': total_pending_registrations,
        
        'total_amount': total_amount,
    }
    
    return render(request, 'administration/flames/courses.html', context)


@login_required
def flames_registrations(request):
    """
    Admin view for managing FLAMES registrations with filtering capability
    """
    registrations = FlamesRegistration.objects.all().select_related('course', 'user', 'team')
    courses = FlamesCourse.objects.all()
    
    # Get stats for dashboard
    total_registrations = registrations.count()
    pending_registrations = registrations.filter(status="Pending").count()
    approved_registrations = registrations.filter(status="Approved").count()
    completed_registrations = registrations.filter(status="Completed").count()
    
    # Get unique colleges for filter (from student profiles)
    colleges = registrations.filter(user__isnull=False).values_list('user__college', flat=True).distinct()
    
    context = {
        'registrations': registrations,
        'courses': courses,
        'colleges': colleges,
        'total_registrations': total_registrations,
        'pending_registrations': pending_registrations,
        'approved_registrations': approved_registrations,
        'completed_registrations': completed_registrations,
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
    # Get filter parameters
    course_id = request.GET.get('course')
    status = request.GET.get('status')
    college = request.GET.get('college')
    mode = request.GET.get('mode', 'all')  # Default to 'all' if not provided
    search = request.GET.get('search[value]')
    year = request.GET.get('year')
    

    # Base queryset
    registrations = FlamesRegistration.objects.all().select_related('course', 'user', 'team')
    
    # Apply filters
    if course_id and course_id != 'all' and course_id != '':
        registrations = registrations.filter(course_id=course_id)
    
    if status and status != 'all' and status != '':
        registrations = registrations.filter(status=status.capitalize())
    
    if college and college != 'all' and college != '':
        registrations = registrations.filter(user__college=college)
    
    if year and year != 'all' and year != '':
        registrations = registrations.filter(year=year)
        
    # Apply mode filter (registration mode)
    if mode and mode != 'all' and mode != '':
        if mode.lower() == 'team':
            registrations = registrations.filter(registration_mode='TEAM')
        elif mode.lower() == 'solo':
            registrations = registrations.filter(registration_mode='SOLO')
    
    # Apply search
    if search:
        registrations = registrations.filter(
            Q(user__first_name__icontains=search) | 
            Q(user__last_name__icontains=search) | 
            Q(user__email__icontains=search) | 
            Q(user__mobile_number__icontains=search) | 
            Q(user__college__icontains=search) | 
            Q(course__title__icontains=search) |
            Q(team__name__icontains=search)
        )
    
    # Get total count before pagination
    total_count = registrations.count()
    
    # Handle sorting
    order_column_index = request.GET.get('order[0][column]')
    order_direction = request.GET.get('order[0][dir]')
    
    if order_column_index and order_direction:
        # Map DataTable column index to model field
        column_mapping = {
            '0': 'id',
            '1': 'user__first_name',  # For full_name
            '2': 'course__title',
            '3': 'user__mobile_number',
            '4': 'user__college',
            '5': 'year',
            '6': 'registration_mode',
            '7': 'team__name',
            '8': 'created_at',
            '9': 'status'
        }
        
        order_field = column_mapping.get(order_column_index)
        if order_field:
            # Apply ordering
            if order_direction == 'desc':
                order_field = f'-{order_field}'
            registrations = registrations.order_by(order_field)
    
    # Pagination
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    registrations = registrations[start:start + length]
    
    # Format data for DataTables
    data = []
    for reg in registrations:
        # Get user information if available
        full_name = ""
        email = ""
        contact_number = ""
        college = ""
        year = ""
        
        if reg.user:
            full_name = f"{reg.user.first_name} {reg.user.last_name}"
            email = reg.user.email
            college = reg.user.college or ""
            contact_number = reg.user.mobile_number
            year = reg.year
        
        # Registration mode and team info
        registration_mode = reg.registration_mode
        team_info = reg.team.name if reg.team else "N/A"
        
        # Referral information
        is_referral = False
        referral_type = "None"
        referral_code = "N/A"
        actual_discount = 0
        
        if reg.referral_code:
            is_referral = True
            referral_type = reg.referral_code.referral_type
            referral_code = reg.referral_code.code
            actual_discount = float(reg.referral_code.discount_amount)
            
            # For team registrations, multiply discount by 5
            if reg.registration_mode == 'TEAM':
                actual_discount *= 5
        
        # Actual amount to pay
        actual_amount_to_pay = float(reg.discounted_price) if reg.discounted_price else float(reg.original_price)
        
        data.append({
            'id': reg.id,
            'full_name': full_name,
            'course': {
                'title': reg.course.title,
                'color': reg.course.icon_color
            },
            'email': email,
            'contact_number': contact_number,
            'college': college,
            'year': year,
            'created_at': reg.created_at.strftime('%d %b %Y, %I:%M %p'),
            'status': reg.status,
            'registration_mode': registration_mode,
            'team': team_info,
            'payment_id': reg.payment_id or "N/A",
            'original_price': float(reg.original_price) if reg.original_price else 0,
            'discounted_price': float(reg.discounted_price) if reg.discounted_price else 0,
            'actual_amount_to_pay': actual_amount_to_pay,
            'is_referral': is_referral,
            'referral_type': referral_type,
            'referral_code': referral_code,
            'actual_discount': actual_discount
        })
    
    # Make sure to return in the format DataTables expects
    return JsonResponse({
        'data': data,
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': FlamesRegistration.objects.count(),
        'recordsFiltered': total_count
    })


@login_required
def admin_registration_details(request):
    """
    Get registration details for modal view
    """
    try:
        reg_id = request.GET.get('id')
        registration = FlamesRegistration.objects.select_related('user', 'course', 'team').get(id=reg_id)
        
        # Get student information
        name = "N/A"
        email = "N/A"
        phone = "N/A"
        college = "N/A"
        year = "N/A"
        
        if registration.user:
            name = f"{registration.user.first_name} {registration.user.last_name}"
            email = registration.user.email
            phone = registration.user.mobile_number
            college = registration.user.college
            year = registration.year
        
        # Team information if applicable
        team_info = {}
        if registration.registration_mode == 'TEAM' and registration.team:
            team = registration.team
            team_info = {
                'id': team.id,
                'name': team.name,
                'status': team.status
            }
            
            # Get team leader
            # if team.leader:
            #     team_info['leader_name'] = f"{team.leader.first_name} {team.leader.last_name}"
            
            # Get team members
            members_list = []
            for member in FlamesTeamMember.objects.filter(team=team):
                if member.member:
                    members_list.append({
                        'name': f"{member.member.first_name} {member.member.last_name}",
                        'email': member.member.email,
                        'is_leader': member.is_leader
                    })
            team_info['members'] = members_list
        
        # Payment and pricing information
        payment_info = {
            'payment_id': registration.payment_id or 'Not available',
            'original_price': float(registration.original_price) if registration.original_price else 0,
            'discounted_price': float(registration.discounted_price) if registration.discounted_price else 0,
            'actual_amount_to_pay': float(registration.discounted_price) if registration.discounted_price else float(registration.original_price),
        }
        
        # Referral information
        referral_info = {}
        if registration.referral_code:
            # Calculate actual discount amount (5x for team registrations)
            actual_discount = float(registration.referral_code.discount_amount)
            if registration.registration_mode == 'TEAM':
                actual_discount *= 5
                
            referral_info = {
                'code': registration.referral_code.code,
                'type': registration.referral_code.referral_type,
                'discount_amount': float(registration.referral_code.discount_amount) if registration.referral_code.discount_amount else 0,
                'actual_discount_amount': actual_discount,
                'is_active': registration.referral_code.is_active,
                'is_referral': True
            }
        else:
            referral_info = {
                'is_referral': False
            }
        
        data = {
            'id': registration.id,
            'name': name,
            'email': email,
            'phone': phone,
            'course_title': registration.course.title,
            'college': college,
            'year': year,
            'message': registration.message or '',
            'status': registration.status,
            'registration_mode': registration.registration_mode,
            'admin_notes': registration.admin_notes or '',
            'created_at': registration.created_at.strftime('%d %b %Y, %I:%M %p'),
            'updated_at': registration.updated_at.strftime('%d %b %Y, %I:%M %p') if registration.updated_at else '',
            'team': team_info,
            'payment': payment_info,
            'referral': referral_info,
            'payment_id': registration.payment_id or 'N/A',
            'payable_amount': float(registration.payable_amount) if registration.payable_amount else 
                              float(registration.discounted_price) if registration.discounted_price else 
                              float(registration.original_price)
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
    status = request.POST.get('status')
    
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