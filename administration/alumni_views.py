from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.views.decorators.http import require_POST
from home.models import Alumni, ReferralCode, FlamesRegistration
from django.utils import timezone
import json

@login_required
def alumni_management(request):
    """
    Admin view for managing alumni
    """
    alumni = Alumni.objects.all().order_by('-created_at')
    
    # Get stats for dashboard
    total_alumni = alumni.count()
    total_referrals = ReferralCode.objects.filter(referral_type='ALUMNI').count()
    total_registrations = FlamesRegistration.objects.filter(referral_code__referral_type='ALUMNI', status="COMPLETED").count()
    
    context = {
        'alumni': alumni,
        'total_alumni': total_alumni,
        'total_referrals': total_referrals,
        'total_registrations': total_registrations,
    }
    
    return render(request, 'administration/alumni/alumni_management.html', context)

@login_required
def alumni_details(request, alumni_id):
    """
    View details of a specific alumni
    """
    alumni = get_object_or_404(Alumni, id=alumni_id)
    referral_codes = ReferralCode.objects.filter(alumni=alumni)
    
    # Get registration stats for this alumni's referral codes
    registrations = FlamesRegistration.objects.filter(referral_code__alumni=alumni)
    
    # Stats
    total_referrals = referral_codes.count()
    active_referrals = referral_codes.filter(is_active=True).count()
    total_registrations = registrations.count()
    total_completed_registrations = registrations.filter(status='COMPLETED').count()
    
    # Calculate total discount amount provided
    total_discount = registrations.filter(status='COMPLETED').aggregate(
        total_discount=Sum('referral_code__discount_amount')
    )['total_discount'] or 0
    
    context = {
        'alumni': alumni,
        'referral_codes': referral_codes,
        'registrations': registrations,
        'total_referrals': total_referrals,
        'active_referrals': active_referrals,
        'total_registrations': total_registrations,
        "total_completed_registrations": total_completed_registrations,
        'total_discount': total_discount,
    }
    
    return render(request, 'administration/alumni/alumni_details.html', context)

@login_required
@require_POST
def add_alumni(request):
    """
    Add a new alumni
    """
    try:
        name = request.POST.get('name')
        email = request.POST.get('email')
        contact_number = request.POST.get('contact_number')
        college = request.POST.get('college')
        batch_year = request.POST.get('batch_year')
        
        # Validate required fields
        if not name or not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Name and email are required'
            })
        
        # Create alumni
        alumni = Alumni.objects.create(
            name=name,
            email=email,
            contact_number=contact_number,
            college=college,
            batch_year=batch_year
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Alumni added successfully',
            'alumni': {
                'id': alumni.id,
                'name': alumni.name,
                'email': alumni.email
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def update_alumni(request, alumni_id):
    """
    Update an existing alumni
    """
    try:
        alumni = get_object_or_404(Alumni, id=alumni_id)
        
        name = request.POST.get('name')
        email = request.POST.get('email')
        contact_number = request.POST.get('contact_number')
        college = request.POST.get('college')
        batch_year = request.POST.get('batch_year')
        
        # Validate required fields
        if not name or not email:
            return JsonResponse({
                'status': 'error',
                'message': 'Name and email are required'
            })
        
        # Update alumni
        alumni.name = name
        alumni.email = email
        alumni.contact_number = contact_number
        alumni.college = college
        alumni.batch_year = batch_year
        alumni.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Alumni updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def delete_alumni(request, alumni_id):
    """
    Delete an alumni
    """
    try:
        alumni = get_object_or_404(Alumni, id=alumni_id)
        alumni.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Alumni deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def generate_referral_code(request, alumni_id):
    """
    Generate a new referral code for an alumni
    """
    try:
        alumni = get_object_or_404(Alumni, id=alumni_id)
        discount_amount = request.POST.get('discount_amount', 500.00)
        
        if not ReferralCode.objects.filter(alumni=alumni).exists():
            code = "FLAME-" + alumni.name[:3].upper()
            
            if ReferralCode.objects.filter(code=code).exists():
                code = "FLAME-" + alumni.name[:3].upper() + str(alumni.id)
        
        else:
            
            import random
            import string
            
            # Generate random string
            prefix = f"FLAME-"
            length = 3
            
            while True:
                # Generate random string of specified length
                random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
                code = f"{prefix}{random_part}"
                
                # Check if code already exists
                if not ReferralCode.objects.filter(code=code).exists():
                    break
        
        # Create referral code
        referral_code = ReferralCode.objects.create(
            code=code,
            referral_type='ALUMNI',
            alumni=alumni,
            discount_amount=discount_amount,
            is_active=True
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Referral code generated successfully',
            'referral_code': {
                'id': referral_code.id,
                'code': referral_code.code,
                'discount_amount': float(referral_code.discount_amount)
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def toggle_referral_code_status(request, code_id):
    """
    Toggle the active status of a referral code
    """
    try:
        referral_code = get_object_or_404(ReferralCode, id=code_id)
        referral_code.is_active = not referral_code.is_active
        referral_code.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Referral code {"activated" if referral_code.is_active else "deactivated"} successfully',
            'is_active': referral_code.is_active
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def update_referral_code(request, code_id):
    """
    Update an existing referral code's code value and discount amount
    """
    try:
        referral_code = get_object_or_404(ReferralCode, id=code_id)
        new_code = request.POST.get('code')
        new_discount_amount = request.POST.get('discount_amount')
        
        # Check if code is changed and if the new code already exists (ignore if it's the same code)
        if new_code != referral_code.code and ReferralCode.objects.filter(code=new_code).exists():
            return JsonResponse({
                'status': 'error',
                'message': f'Referral code {new_code} already exists. Please choose a different code.'
            })
        
        # Update the referral code
        referral_code.code = new_code
        referral_code.discount_amount = new_discount_amount
        referral_code.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Referral code updated successfully',
            'referral_code': {
                'id': referral_code.id,
                'code': referral_code.code,
                'discount_amount': float(referral_code.discount_amount)
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def alumni_stats(request):
    """
    Get statistics for alumni referrals
    """
    # Get all alumni with their referral stats
    alumni_with_stats = Alumni.objects.annotate(
        total_referrals=Count('referral_codes'),
        active_referrals=Count('referral_codes', filter=Q(referral_codes__is_active=True)),
        total_registrations=Count('referral_codes__registrations', filter=Q(referral_codes__registrations__status='COMPLETED')),
        total_discount=Sum('referral_codes__registrations__referral_code__discount_amount', filter=Q(referral_codes__registrations__status='COMPLETED'))
    ).order_by('-total_registrations')
    
    # Prepare data for the chart
    alumni_names = []
    registration_counts = []
    discount_amounts = []
    
    for alumni in alumni_with_stats[:10]:  # Top 10 alumni by registrations
        alumni_names.append(alumni.name)
        registration_counts.append(alumni.total_registrations)
        discount_amounts.append(float(alumni.total_discount or 0))
    
    data = {
        'alumni_names': alumni_names,
        'registration_counts': registration_counts,
        'discount_amounts': discount_amounts,
        'alumni_with_stats': [
            {
                'id': alumni.id,
                'name': alumni.name,
                'email': alumni.email,
                'total_referrals': alumni.total_referrals,
                'active_referrals': alumni.active_referrals,
                'total_registrations': alumni.total_registrations,
                'total_discount': float(alumni.total_discount or 0)
            }
            for alumni in alumni_with_stats
        ]
    }
    
    return JsonResponse({
        'status': 'success',
        'data': data
    })

@login_required
def alumni_list_ajax(request):
    """
    AJAX endpoint for getting alumni data for DataTable
    """
    try:
        # Get request parameters
        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')
        
        # Base queryset
        queryset = Alumni.objects.all()
        
        # Apply search filter
        if search_value:
            queryset = queryset.filter(
                Q(name__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(college__icontains=search_value) |
                Q(batch_year__icontains=search_value)
            )
        
        # Get total record count
        total_count = Alumni.objects.count()
        filtered_count = queryset.count()
        
        # Apply pagination
        queryset = queryset.order_by('-created_at')[start:start + length]
        
        # Annotate with stats
        queryset = queryset.annotate(
            total_referrals=Count('referral_codes'),
            total_registrations=Count('referral_codes__registrations')
        )
        
        # Prepare data
        data = []
        for alumni in queryset:
            data.append({
                'id': alumni.id,
                'name': alumni.name,
                'email': alumni.email,
                'contact_number': alumni.contact_number or 'N/A',
                'college': alumni.college or 'N/A',
                'batch_year': alumni.batch_year or 'N/A',
                'total_referrals': alumni.total_referrals,
                'total_registrations': alumni.total_registrations,
                'created_at': alumni.created_at.strftime('%d %b %Y')
            })
        
        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': filtered_count,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })
