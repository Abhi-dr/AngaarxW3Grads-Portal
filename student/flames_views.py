from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from home.models import FlamesCourse, FlamesRegistration, FlamesTeam, FlamesTeamMember

@login_required
def student_flames(request):

    registrations = FlamesRegistration.objects.filter(
        user=request.user
    ).select_related('course', 'team').order_by('-created_at')
        
    # Prefetch team members for teams the student is part of
    for registration in registrations:
        if registration.team:
            registration.team.members_list = FlamesTeamMember.objects.filter(team=registration.team)
    
    # Get available courses (courses that the student hasn't registered for)
    registered_course_ids = registrations.values_list('course_id', flat=True)
    available_courses = FlamesCourse.objects.filter(is_active=True).exclude(id__in=registered_course_ids)
    
    parameters = {
        'registrations': registrations,
        'available_courses': available_courses,
        'active_tab': 'flames'
    }
    
    return render(request, 'student/flames/flames.html', parameters)

@login_required
def team_formation(request):
    """
    Manage team formation for solo registrations
    """
    # Get student's solo registrations that don't have a team yet
    solo_registrations = FlamesRegistration.objects.filter(
        user=request.user,
        registration_mode='SOLO',
        team__isnull=True
    ).select_related('course')
    
    # Get student's teams
    teams = FlamesTeam.objects.filter(
        team_leader=request.user
    ).prefetch_related('members')
    
    context = {
        'solo_registrations': solo_registrations,
        'teams': teams,
        'active_tab': 'flames_teams'
    }
    
    return render(request, 'student/flames/team_formation.html', context)

@login_required
def create_team(request, registration_id):
    """
    Create a team for a solo registration
    """
    registration = get_object_or_404(
        FlamesRegistration, 
        id=registration_id, 
        user=request.user, 
        registration_mode='SOLO',
        team__isnull=True
    )
    
    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        
        if not team_name:
            messages.error(request, "Team name is required.")
            return redirect('student_team_formation')
        
        # Create the team
        team = FlamesTeam.objects.create(
            name=team_name,
            team_leader=request.user,
            course=registration.course
        )
        
        # Link the registration to the team
        registration.team = team
        registration.save()
        
        # Add the user as the first team member
        FlamesTeamMember.objects.create(
            team=team,
            full_name=registration.full_name,
            email=registration.email,
            contact_number=registration.contact_number,
            user=request.user,
            is_leader=True
        )
        
        messages.success(request, f"Team '{team_name}' created successfully!")
        return redirect('student_team_formation')
    
    # GET request
    return render(request, 'student/flames/create_team.html', {
        'registration': registration,
        'active_tab': 'flames_teams'
    })

@login_required
def add_team_member(request, team_id):
    """
    Add a team member to an existing team
    """
    team = get_object_or_404(FlamesTeam, id=team_id, team_leader=request.user)
    
    # Check if team is already full
    if team.members.count() >= 5:
        messages.error(request, "This team already has the maximum number of members (5).")
        return redirect('student_team_formation')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        contact_number = request.POST.get('contact_number')
        
        if not all([full_name, email, contact_number]):
            messages.error(request, "All fields are required.")
            return redirect('student_add_team_member', team_id=team.id)
        
        # Check if email is already in the team
        if team.members.filter(email=email).exists():
            messages.error(request, f"A member with email '{email}' is already in this team.")
            return redirect('student_add_team_member', team_id=team.id)
        
        # Add new team member
        FlamesTeamMember.objects.create(
            team=team,
            full_name=full_name,
            email=email,
            contact_number=contact_number
        )
        
        messages.success(request, f"{full_name} has been added to the team.")
        return redirect('student_team_formation')
    
    # GET request
    return render(request, 'student/flames/add_team_member.html', {
        'team': team,
        'active_tab': 'flames_teams'
    })

@login_required
def remove_team_member(request, member_id):
    """
    Remove a team member from a team
    """
    # Only allow removal if the user is the team leader and the member is not the leader
    member = get_object_or_404(
        FlamesTeamMember, 
        id=member_id, 
        team__team_leader=request.user,
        is_leader=False
    )
    
    team = member.team
    member_name = member.full_name
    
    # Delete the member
    member.delete()
    
    messages.success(request, f"{member_name} has been removed from the team.")
    return redirect('student_team_formation')
