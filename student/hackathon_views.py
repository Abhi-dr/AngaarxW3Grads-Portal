from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.db import IntegrityError
from django.core.paginator import Paginator

from .hackathon_models import HackathonTeam, TeamMember, JoinRequest, TeamInvite
from accounts.models import Student

import json


@login_required(login_url="login")
def hackathon_dashboard(request):
    """Main view for the hackathon team maker dashboard"""
    student = request.user.student
    
    # Check if student is already a team leader
    led_team = HackathonTeam.objects.filter(leader=student).first()
    
    # Check if student is already a team member
    team_membership = TeamMember.objects.filter(student=student).first()
    
    # Get pending join requests sent by the student
    pending_requests = JoinRequest.objects.filter(student=student, status='pending')
    
    # Get pending team invites received by the student
    received_invites = TeamInvite.objects.filter(student=student, status='pending')
    
    # If student is a team leader, get join requests for their team
    team_requests = None
    if led_team:
        team_requests = JoinRequest.objects.filter(team=led_team, status='pending')
    
    context = {
        'led_team': led_team,
        'team_membership': team_membership,
        'pending_requests': pending_requests,
        'team_requests': team_requests,
        'received_invites': received_invites,
    }
    
    return render(request, 'student/hackathon/hackathon.html', context)

# ================================= CREATE TEAM =================================

@login_required(login_url="login")
def create_team(request):
    """View for creating a new hackathon team"""
    student = request.user.student
    
    # Check if student is already a team leader or member
    if HackathonTeam.objects.filter(leader=student).exists():
        messages.error(request, "You are already leading a team!")
        return redirect('hackathon_dashboard')
    
    if TeamMember.objects.filter(student=student).exists():
        messages.error(request, "You are already a member of a team!")
        return redirect('hackathon_dashboard')
    
    if request.method == 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description')
            members_limit = data.get('members_limit', 4)
            status = data.get('status', 'open')
            required_skills = data.get('required_skills', [])
            
            # Validate data
            if not name or not description:
                return JsonResponse({'status': 'error', 'message': 'Name and description are required'}, status=400)
            
            # Check if team name already exists
            if HackathonTeam.objects.filter(name=name).exists():
                return JsonResponse({'status': 'error', 'message': 'Team name already exists'}, status=400)
            
            # Create team
            team = HackathonTeam.objects.create(
                name=name,
                description=description,
                leader=student,
                members_limit=members_limit,
                status=status,
                required_skills=required_skills
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Team created successfully',
                'team_id': team.id,
                'redirect': '/dashboard/hackathon/'
            })
        else:
            # Handle non-AJAX POST request
            name = request.POST.get('name')
            description = request.POST.get('description')
            members_limit = request.POST.get('members_limit', 4)
            status = request.POST.get('status', 'open')
            required_skills = request.POST.getlist('required_skills', [])
            
            # Validate data
            if not name or not description:
                messages.error(request, "Name and description are required")
                return redirect('create_team')
            
            # Check if team name already exists
            if HackathonTeam.objects.filter(name=name).exists():
                messages.error(request, "Team name already exists")
                return redirect('create_team')
            
            # Create team
            HackathonTeam.objects.create(
                name=name,
                description=description,
                leader=student,
                members_limit=members_limit,
                status=status,
                required_skills=required_skills
            )
            
            messages.success(request, "Team created successfully")
            return redirect('hackathon_dashboard')
    
    return render(request, 'student/hackathon/create_team.html')

# ================================= MANAGE TEAM =================================

@login_required(login_url="login")
def manage_team(request, slug):
    """View for managing a hackathon team (for team leaders)"""
    student = request.user.student
    team = get_object_or_404(HackathonTeam, slug=slug)
    
    # Check if student is the team leader
    if team.leader != student:
        messages.error(request, "You are not authorized to manage this team")
        return redirect('hackathon_dashboard')
    
    # Get team members
    team_members = TeamMember.objects.filter(team=team)
    
    # Get pending join requests
    join_requests = JoinRequest.objects.filter(team=team, status='pending')
    
    # Get sent invites
    sent_invites = TeamInvite.objects.filter(team=team, status='pending')
    
    context = {
        'team': team,
        'team_members': team_members,
        'join_requests': join_requests,
        'sent_invites': sent_invites,
    }
    
    return render(request, 'student/hackathon/manage_team.html', context)

# ================================= UPDATE TEAM =================================

@login_required(login_url="login")
def update_team(request, slug):
    """AJAX view for updating team details"""
    student = request.user.student
    team = get_object_or_404(HackathonTeam, slug=slug)
    
    # Check if student is the team leader
    if team.leader != student:
        return JsonResponse({'status': 'error', 'message': 'You are not authorized to update this team'}, status=403)
    
    if request.method == 'POST':
        data = request.POST
        
        # Update team details
        team.name = data.get('name', team.name)
        team.description = data.get('description', team.description)
        team.members_limit = data.get('members_limit', team.members_limit)
        team.status = data.get('status', team.status)
        team.required_skills = json.loads(data.get('required_skills', '[]'))
        team.save()
        
        messages.success(request, 'Team updated successfully')
        return redirect('manage_team', slug=slug)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

# ================================= DELETE TEAM =================================

@login_required(login_url="login")
def delete_team(request, team_id):
    """AJAX view for deleting a team"""
    student = request.user.student
    team = get_object_or_404(HackathonTeam, id=team_id)
    
    # Check if student is the team leader
    if team.leader != student:
        return JsonResponse({'status': 'error', 'message': 'You are not authorized to delete this team'}, status=403)
    
    if request.method == 'POST':
        # Delete team
        team.delete()
        
        messages.success(request, 'Team deleted successfully')
        return redirect('hackathon_dashboard')
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required(login_url="login")
def list_teams(request):
    """View for listing all available teams"""
    student = request.user.student
    
    # Get query parameters for filtering
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'open')
    skill_filter = request.GET.get('skill', '')
    
    # Base query: only show open teams by default
    teams_query = HackathonTeam.objects.filter(status='open')
    
    # Apply search filter if provided
    if search_query:
        teams_query = teams_query.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Apply status filter if not 'all'
    if status_filter != 'all':
        teams_query = teams_query.filter(status=status_filter)
    
    # Apply skill filter if provided
    if skill_filter:
        # Filter teams that have the required skill
        teams_query = [team for team in teams_query if skill_filter.lower() in [s.lower() for s in team.required_skills]]
    
    # Order by creation date (newest first)
    teams = sorted(teams_query, key=lambda t: t.created_at, reverse=True)
    
    # Paginate results
    paginator = Paginator(teams, 10)  # Show 10 teams per page
    page_number = request.GET.get('page', 1)
    teams_page = paginator.get_page(page_number)
    
    # Check if student is already in a team (as leader or member)
    is_in_team = HackathonTeam.objects.filter(leader=student).exists() or TeamMember.objects.filter(student=student).exists()
    
    # Get all pending and rejected join requests by the student
    pending_requests = JoinRequest.objects.filter(student=student, status='pending').values_list('team_id', flat=True)
    rejected_requests = JoinRequest.objects.filter(student=student, status='rejected').values_list('team_id', flat=True)
    
    context = {
        'teams': teams_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'skill_filter': skill_filter,
        'is_in_team': is_in_team,
        'pending_requests': list(pending_requests),
        'rejected_requests': list(rejected_requests),
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Return JSON response for AJAX requests
        teams_data = []
        for team in teams_page:
            teams_data.append({
                'id': team.id,
                'name': team.name,
                'description': team.description,
                'leader': f"{team.leader.first_name} {team.leader.last_name}",
                'members_count': team.current_members_count(),
                'members_limit': team.members_limit,
                'status': team.status,
                'required_skills': team.required_skills,
                'created_at': team.created_at.strftime('%Y-%m-%d %H:%M'),
                'has_pending_request': team.id in pending_requests,
                'is_rejected': team.id in rejected_requests,
            })
        
        return JsonResponse({
            'teams': teams_data,
            'has_next': teams_page.has_next(),
            'has_previous': teams_page.has_previous(),
            'page_number': teams_page.number,
            'num_pages': teams_page.paginator.num_pages,
        })
    
    return render(request, 'student/hackathon/list_teams.html', context)

@login_required(login_url="login")
def team_detail(request, slug):
    """View for displaying team details"""
    student = request.user.student
    team = get_object_or_404(HackathonTeam, slug=slug)
    
    # Get team members
    team_members = TeamMember.objects.filter(team=team)
    
    # Check if student has already sent a join request
    join_request = JoinRequest.objects.filter(team=team, student=student).first()
    has_pending_request = join_request and join_request.status == 'pending'
    is_rejected = join_request and join_request.status == 'rejected'
    
    # Check if student is already in a team (as leader or member)
    is_in_team = HackathonTeam.objects.filter(leader=student).exists() or TeamMember.objects.filter(student=student).exists()
    
    # Check if student is the team leader
    is_team_leader = team.leader == student
    
    # Check if student is a member of this specific team
    is_team_member = TeamMember.objects.filter(team=team, student=student).exists()
    
    # Get all pending join requests by the student
    pending_requests = JoinRequest.objects.filter(student=student, status='pending').values_list('team_id', flat=True)
    
    context = {
        'team': team,
        'team_members': team_members,
        'has_pending_request': has_pending_request,
        'is_rejected': is_rejected,
        'is_in_team': is_in_team,
        'is_team_leader': is_team_leader,
        'is_team_member': is_team_member,
        'pending_requests': list(pending_requests),
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Return JSON response for AJAX requests
        team_data = {
            'id': team.id,
            'name': team.name,
            'description': team.description,
            'leader': {
                'id': team.leader.id,
                'name': f"{team.leader.first_name} {team.leader.last_name}",
                'username': team.leader.username,
            },
            'members_count': team.current_members_count(),
            'members_limit': team.members_limit,
            'status': team.status,
            'required_skills': team.required_skills,
            'created_at': team.created_at.strftime('%Y-%m-%d %H:%M'),
            'has_pending_request': has_pending_request,
            'is_rejected': is_rejected,
            'is_in_team': is_in_team,
            'members': [],
        }
        
        # Add team members data
        for member in team_members:
            team_data['members'].append({
                'id': member.student.id,
                'name': f"{member.student.first_name} {member.student.last_name}",
                'username': member.student.username,
                'joined_at': member.joined_at.strftime('%Y-%m-%d %H:%M'),
            })
        
        return JsonResponse(team_data)
    
    return render(request, 'student/hackathon/team_detail.html', context)


@login_required(login_url="login")
def send_join_request(request, team_id):
    """AJAX view for sending a join request to a team"""
    student = request.user.student
    team = get_object_or_404(HackathonTeam, id=team_id)
    
    # Check if team is open for join requests
    if team.status != 'open':
        return JsonResponse({'status': 'error', 'message': 'This team is not accepting new members'}, status=400)
    
    # Check if team is full
    if team.is_full():
        return JsonResponse({'status': 'error', 'message': 'This team is already full'}, status=400)
    
    # Check if student is already in a team (as leader or member)
    if HackathonTeam.objects.filter(leader=student).exists() or TeamMember.objects.filter(student=student).exists():
        return JsonResponse({'status': 'error', 'message': 'You are already in a team'}, status=400)
    
    # Check if student has already sent a join request
    join_request = JoinRequest.objects.filter(team=team, student=student).first()
    if join_request:
        if join_request.status == 'pending':
            return JsonResponse({'status': 'error', 'message': 'You have already sent a join request to this team'}, status=400)
        elif join_request.status == 'rejected':
            return JsonResponse({'status': 'error', 'message': 'Your previous join request was rejected'}, status=400)
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = json.loads(request.body)
        message = data.get('message', '')
        
        # Create join request
        join_request = JoinRequest.objects.create(
            team=team,
            student=student,
            message=message,
            status='pending'
        )
        
        return JsonResponse({'status': 'success', 'message': 'Join request sent successfully'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required(login_url="login")
def cancel_join_request(request, request_id):
    """AJAX view for canceling a join request"""
    student = request.user.student
    join_request = get_object_or_404(JoinRequest, id=request_id, student=student)
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Delete join request
        join_request.delete()
        
        return JsonResponse({'status': 'success', 'message': 'Join request canceled successfully'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required(login_url="login")
def handle_join_request(request, request_id, action):
    """AJAX view for handling (approving/rejecting) a join request"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    
    join_request = get_object_or_404(JoinRequest, id=request_id)
    
    # Check if user is team leader
    if request.user.student != join_request.team.leader:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    if join_request.status != 'pending':
        return JsonResponse({'status': 'error', 'message': 'This request has already been handled'}, status=400)
    
    try:
        if action == 'approve':
            # Check if team is full
            if join_request.team.is_full():
                join_request.status = 'rejected'
                join_request.save()
                return JsonResponse({'status': 'error', 'message': 'Team is full'}, status=400)
            
            # Check if student is already in another team
            if TeamMember.objects.filter(student=join_request.student).exists():
                join_request.status = 'rejected'
                join_request.save()
                return JsonResponse({'status': 'error', 'message': 'Student is already in another team'}, status=400)
            
            # Create team membership
            TeamMember.objects.create(
                team=join_request.team,
                student=join_request.student
            )
            join_request.status = 'approved'
            join_request.save()
            
            return JsonResponse({'status': 'success', 'message': 'Join request approved successfully'})
            
        elif action == 'reject':
            join_request.status = 'rejected'
            join_request.save()
            return JsonResponse({'status': 'success', 'message': 'Join request rejected successfully'})
        
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
            
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url="login")
def remove_team_member(request, team_id, member_id):
    """AJAX view for removing a team member"""
    student = request.user.student
    team = get_object_or_404(HackathonTeam, id=team_id)
    
    # Check if student is the team leader
    if team.leader != student:
        return JsonResponse({'status': 'error', 'message': 'You are not authorized to remove team members'}, status=403)
    
    # Get the team member
    member = get_object_or_404(TeamMember, team=team, student_id=member_id)   
    member.delete()
    
    messages.success(request, "Team member removed successfully!")
        
    return redirect("manage_team", slug=team.slug)


@login_required(login_url="login")
def leave_team(request, team_id):
    """AJAX view for leaving a team"""
    student = request.user.student
    team = get_object_or_404(HackathonTeam, id=team_id)
    
    # Check if student is a team member
    team_member = get_object_or_404(TeamMember, team=team, student=student)
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Remove team member
        team_member.delete()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'You have left the team successfully',
            'redirect': '/dashboard/hackathon/'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required(login_url="login")
def get_all_skills(request):
    """AJAX view for getting all available skills"""
    # This is a placeholder - in a real implementation, you might have a Skills model
    # or fetch skills from an API
    skills = [
        "Python", "JavaScript", "React", "Django", "Node.js", "Angular", "Vue.js",
        "HTML", "CSS", "Java", "C++", "C#", "PHP", "Ruby", "Swift", "Kotlin",
        "Flutter", "React Native", "Machine Learning", "Data Science", "AI",
        "Blockchain", "Cloud Computing", "DevOps", "UI/UX Design", "Product Management"
    ]
    
    return JsonResponse({'skills': skills})


@login_required(login_url="login")
def search_students(request):
    query = request.GET.get('query', '')
    team_id = request.GET.get('team_id', None)
    
    if query:
        students = Student.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query)
        ).exclude(id=request.user.student.id)
        
        results = []
        for student in students:
            results.append({
                'id': student.id,
                'name': f"{student.first_name} {student.last_name}",
                'username': student.username,
                'email': student.email,
            })
        
        return JsonResponse({'status': 'success', 'results': results})
    
    return JsonResponse({'status': 'error', 'message': 'No query provided'}, status=400)

@login_required(login_url="login")
def send_team_invite(request, team_id):
    """AJAX view for sending a team invite"""
    student = request.user.student
    team = get_object_or_404(HackathonTeam, id=team_id)
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        message = request.POST.get('message', '')
        
        if not student_id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Student ID is required'}, status=400)
            messages.error(request, 'Student ID is required')
            return redirect('manage_team', slug=team.slug)
        
        invited_student = get_object_or_404(Student, id=student_id)
        
        # Check if student is already in a team
        if TeamMember.objects.filter(student=invited_student).exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Student is already in a team'}, status=400)
            messages.error(request, 'Student is already in a team')
            return redirect('manage_team', slug=team.slug)
        
        # Check if team is full
        if team.is_full():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Team is full'}, status=400)
            messages.error(request, 'Team is full')
            return redirect('manage_team', slug=team.slug)
        
        # Check if invite already exists
        if TeamInvite.objects.filter(team=team, student=invited_student, status='pending').exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Invite already sent'}, status=200)
            messages.info(request, 'Invite already sent')
            return redirect('manage_team', slug=team.slug)
        
        try:
            # Create team invite
            TeamInvite.objects.create(
                team=team,
                student=invited_student,
                message=message
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success', 
                    'message': f'Invite sent to {invited_student.first_name} {invited_student.last_name}'
                })
            messages.success(request, f'Invite sent to {invited_student.first_name} {invited_student.last_name}')
            return redirect('manage_team', slug=team.slug)
        except IntegrityError:
            # Handle the case where a duplicate invite is attempted
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Invite already sent'}, status=200)
            messages.info(request, 'Invite already sent')
            return redirect('manage_team', slug=team.slug)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required(login_url="login")
def handle_team_invite(request, invite_id, action):
    """AJAX view for handling (accepting/rejecting) a team invite"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'})
    
    if action not in ['accept', 'reject']:
        return JsonResponse({'status': 'error', 'message': 'Invalid action'})
    
    invite = get_object_or_404(TeamInvite, id=invite_id)
    if request.user.student != invite.student:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'})
    
    if invite.status != 'pending':
        return JsonResponse({'status': 'error', 'message': 'Invite is no longer pending'})
    
    try:
        if action == 'accept':
            # Check if student is already in a team
            if TeamMember.objects.filter(student=invite.student).exists():
                invite.delete()
                return JsonResponse({'status': 'error', 'message': 'You are already in a team'})
            
            # Check if team is full
            if invite.team.is_full():
                invite.delete()
                return JsonResponse({'status': 'error', 'message': 'Team is full'})
            
            # Create team membership
            TeamMember.objects.create(
                team=invite.team,
                student=invite.student
            )
            invite.status = 'accepted'
            invite.save()
            
            return JsonResponse({
                'status': 'success',
                'message': f'You have joined {invite.team.name}',
                'redirect': f'/dashboard/hackathon/team/{invite.team.slug}/'
            })
        else:
            invite.status = 'rejected'
            invite.save()
            return JsonResponse({
                'status': 'success',
                'message': f'Invite from {invite.team.name} rejected'
            })
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required(login_url="login")
def cancel_team_invite(request, invite_id):
   
    invite = get_object_or_404(TeamInvite, id=invite_id)
    if request.user.student != invite.team.leader:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'})
    
    if invite.status != 'pending':
        return JsonResponse({'status': 'error', 'message': 'Invite is no longer pending'})
    
    try:
        invite.delete()
        messages.success(request, 'Invite canceled successfully')
        return redirect('manage_team', slug=invite.team.slug)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
