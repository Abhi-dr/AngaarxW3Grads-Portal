from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Article, Comment, FlamesCourse, FlamesCourseTestimonial, FlamesRegistration
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count
from practice.models import Batch, Submission, Question
import requests
import time
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .flareModel import FlareRegistration
import json

from administration.models import Achievement

# ======================================= FLARE REGISTRATION ================================

def flare(request):
    return render(request, 'home/flare.html')


def flare_registration_view(request):
    """Display the FLARE registration form"""
    return render(request, 'home/flareRegistration.html')


def flare_registration_submit(request):
    """Handle FLARE registration form submission"""
    if request.method == 'POST':
        try:
            # Extract form data
            email = request.POST.get('email', '').strip()
            full_name = request.POST.get('full_name', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()
            occupation_status = request.POST.get('occupation_status', '').strip()
            current_year = request.POST.get('current_year', '').strip()
            motivation = request.POST.get('motivation', '').strip()
            commitment = request.POST.get('commitment') == 'true'
            
            # Get multi-select fields
            courses = request.POST.getlist('courses')
            career_goals = request.POST.getlist('career_goals')
            
            # Server-side validation
            errors = []
            
            # Email validation
            if not email or '@' not in email:
                errors.append('Invalid email address')
            
            # Check if email already exists
            if FlareRegistration.objects.filter(email=email).exists():
                errors.append('This email is already registered')
            
            # Phone validation (10 digits)
            if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
                errors.append('Phone number must be 10 digits')
            
            # Name validation
            if not full_name or len(full_name) < 2:
                errors.append('Please enter your full name')
            
            # Occupation validation
            if not occupation_status:
                errors.append('Please select your occupation status')
            
            # Year validation for students
            student_occupations = ['school_student', 'undergrad_student', 'postgrad_student']
            if occupation_status in student_occupations and not current_year:
                errors.append('Please enter your current year of study')
            
            # Courses validation
            if not courses or len(courses) == 0:
                errors.append('Please select at least one course')
            
            # Career goals validation
            if not career_goals or len(career_goals) == 0:
                errors.append('Please select at least one career goal')

            # Commitment validation
            if not commitment:
                errors.append('You must commit to the program')
            
            # If there are errors, return to form with error messages
            if errors:
                for error in errors:
                    messages.error(request, error)
                return redirect('flare_registration')
            
            # Create the registration
            registration = FlareRegistration()
            registration.email = email
            registration.full_name = full_name
            registration.phone_number = phone_number
            registration.occupation_status = occupation_status
            registration.current_year = current_year if current_year else None
            registration.motivation = motivation
            registration.commitment = commitment
            
            # Set multi-select fields as JSON
            registration.set_courses_list(courses)
            registration.set_career_goals_list(career_goals)
            
            # Save to database
            registration.save()
            
            # Redirect to success page
            return redirect('flare_registration_success')
            
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('flare_registration')
    
    # If not POST, redirect back to form
    return redirect('flare_registration')


def flare_registration_success(request):
    """Display success page after registration"""
    return render(request, 'home/flareRegistrationSuccess.html')

