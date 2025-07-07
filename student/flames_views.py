from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from home.models import FlamesCourse, FlamesRegistration, FlamesTeam, FlamesTeamMember, Session, FlamesScrum

from django.utils import timezone

# ======================================= FLAMES MAIN PAGE ================================

@login_required(login_url='login')
def student_flames(request):
    # Get registrations where the user is directly registered
    direct_registrations = FlamesRegistration.objects.filter(
        user=request.user
    ).select_related('course', 'team').order_by('-created_at')
    
    # Find teams where the user is a member but not the team leader
    team_memberships = FlamesTeamMember.objects.filter(
        member=request.user,
        is_leader=False
    ).select_related('team')
    
    team_ids = team_memberships.values_list('team_id', flat=True)
    
    # Get registrations for teams where the user is a member
    team_registrations = FlamesRegistration.objects.filter(
        team_id__in=team_ids
    ).select_related('course', 'team').order_by('-created_at')
    
    # Combine both types of registrations
    registrations = list(direct_registrations)
    
    # Add team registrations if they're not already included
    for reg in team_registrations:
        if reg not in registrations:
            registrations.append(reg)
    
    # Sort by created_at (most recent first)
    registrations.sort(key=lambda x: x.created_at, reverse=True)
    
    # Prefetch team members for all registrations with teams
    for registration in registrations:
        if registration.team:
            registration.team.members_list = FlamesTeamMember.objects.filter(team=registration.team)
    
    # Get available courses (courses that the student hasn't registered for)
    registered_course_ids = set()
    for reg in registrations:
        registered_course_ids.add(reg.course_id)
    
    available_courses = FlamesCourse.objects.filter(is_active=True).exclude(id__in=registered_course_ids)
    
    parameters = {
        'registrations': registrations,
        'available_courses': available_courses,
        'active_tab': 'flames'
    }
    
    return render(request, 'student/flames/flames.html', parameters)


# ====================================== VIEW REGISTRATION ================================

@login_required(login_url='login')
def view_registration(request, slug):
    course = get_object_or_404(FlamesCourse, slug=slug)
    
    # Get the registration with related course data
    registration = FlamesRegistration.objects.filter(
        user=request.user,
        course=course
    ).select_related('course', 'team', 'referral_code').first()
    
    # If not found, check if the user is a team member
    if not registration:
        # Check if user is part of a team registered for this course
        from home.models import FlamesTeamMember
        team_memberships = FlamesTeamMember.objects.filter(
            member=request.user,
            team__registrations__course=course
        ).select_related('team')
        
        if team_memberships.exists():
            # Get the registration through the team
            team = team_memberships.first().team
            registration = FlamesRegistration.objects.filter(
                team=team,
                course=course
            ).select_related('course', 'team', 'referral_code').first()
        else:
            messages.error(request, "You are not registered for this course.")
            return redirect('student_flames')
    
    # If this is a team registration, prefetch team members
    if registration.registration_mode == 'TEAM' and registration.team:
        from django.db.models import Prefetch
        from home.models import FlamesTeamMember
        
        # Prefetch team members with their student information
        team_members = FlamesTeamMember.objects.filter(
            team=registration.team
        ).select_related('member')
        
        # Attach the members to the team object
        registration.team.members_list = team_members
    
    parameters = {
        'registration': registration,
        'course': course,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    
    return render(request, 'student/flames/view_registration.html', parameters)


# ========================================= MY COURSE =====================================

@login_required(login_url='login')
def my_course(request, slug):
    course = get_object_or_404(FlamesCourse, slug=slug)

    # Try to get direct registration
    registration = FlamesRegistration.objects.select_related('course', 'team').filter(
        user=request.user,
        course=course,
        status__in=['Approved', 'Completed']
    ).first()

    # If not directly registered, check team membership
    team_registration = None
    if not registration:
        team_registration = FlamesTeamMember.objects.select_related('team__course').filter(
            member=request.user,
            team__registrations__course=course,
            team__registrations__status__in=['Approved', 'Completed']
        ).first()

        if not team_registration:
            messages.error(request, "You are not registered for this course.")
            return redirect('student_flames')

    # Use whichever is available (priority to individual registration)
    effective_registration = registration or team_registration.team.registrations.get(course=course)

    # Check for special bundle course (id=8)
    if course.id == 8:  # Bundle: DSA (3) + Full Stack (4)
        dsa_sessions = Session.objects.filter(course_id=3).order_by('start_datetime')
        full_stack_sessions = Session.objects.filter(course_id=4).order_by('start_datetime')

        parameters = {
            'registration': effective_registration,
            'course': course,
            'dsa_sessions': dsa_sessions,
            'full_stack_sessions': full_stack_sessions,
        }
    else:
        sessions = Session.objects.filter(course=course).order_by('start_datetime')

        parameters = {
            'registration': effective_registration,
            'course': course,
            'sessions': sessions,
        }

    return render(request, 'student/flames/my_course.html', parameters)


# ========================================= UPDATE TEAM PROJECT =============================

def update_team_project(request, team_id):
    team = get_object_or_404(FlamesTeam, id=team_id)

    if request.method == 'POST':
        team.project_title = request.POST.get('project_title', '').strip()
        team.project_description = request.POST.get('project_description', '').strip()
        team.project_link = request.POST.get('project_link', '').strip()
        team.save()
        messages.success(request, "Project details updated successfully!")
        return redirect('flames_my_course', team.course.slug)
    
# ========================================= TEAM SCRUM VIEW =============================

@login_required(login_url='login')
def team_scrum_view(request, team_id):
    team = get_object_or_404(FlamesTeam, id=team_id)

    # Check if the user is part of this team
    is_member = FlamesTeamMember.objects.filter(team=team, member=request.user).exists()
    if not is_member:
        messages.error(request, "You're not a member of this team.")
        return redirect('student_flames')

    is_leader = FlamesTeamMember.objects.filter(team=team, member=request.user, is_leader=True).exists()
    today = timezone.now().date()

    # Check if today's scrum exists
    today_scrum = FlamesScrum.objects.filter(team=team, date=today).first()

    # Handle form submission
    if request.method == 'POST' and is_leader and not today_scrum:
        what_done = request.POST.get('what_done')
        what_doing = request.POST.get('what_doing')
        any_issues = request.POST.get('any_issues')
        something_more = request.POST.get('something_more', '')

        FlamesScrum.objects.create(
            team=team,
            date=today,
            what_done=what_done,
            what_doing=what_doing,
            any_issues=any_issues,
            something_more=something_more,
            filled_by=request.user.student if hasattr(request.user, 'student') else None
        )

        messages.success(request, "✅ Today's Scrum submitted successfully!")
        return redirect('team_scrum', team_id=team.id)

    # Past scrums (excluding today)
    past_scrums = FlamesScrum.objects.filter(team=team).exclude(date=today).order_by('-date')

    return render(request, 'student/flames/scrums.html', {
        'team': team,
        'today': today,
        'today_scrum': today_scrum,
        'past_scrums': past_scrums,
        'is_leader': is_leader,
    })



