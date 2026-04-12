from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import FlamesCourse, FlamesCourseTestimonial, FlamesRegistration, ReferralCode, FlamesTeam, FlamesTeamMember, FlamesEdition
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from accounts.models import CustomUser
from django_ratelimit.decorators import ratelimit

# ===================================== FLAMES PAGE ==============================

def flames(request):
    try:
        active_edition = FlamesEdition.objects.get(is_active=True)
        courses = FlamesCourse.objects.filter(edition=active_edition, is_active=True)
    except FlamesEdition.DoesNotExist:
        # Fallback: show all active courses if no edition is set as active
        active_edition = None
        courses = FlamesCourse.objects.filter(is_active=True)
    return render(request, "home/flames.html", {
        'courses': courses,
        'edition': active_edition,
    })

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


# ============================= VALIDATE REFERRAL CODE ==========================

@ratelimit(key='ip', rate='30/m', method=['GET'], block=False)
def validate_referral(request):
    """Validate referral code and return price details."""
    if getattr(request, 'limited', False):
        return JsonResponse({'status': 'error', 'message': 'Too many validation attempts. Please try again shortly.'}, status=429)

    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

    code              = request.GET.get('code', '')
    course_id         = request.GET.get('course_id', '')
    registration_mode = request.GET.get('registration_mode', '')

    if not code or not course_id:
        return JsonResponse({'status': 'error', 'message': 'Missing required parameters.'}, status=400)

    try:
        course = FlamesCourse.objects.get(id=course_id, is_active=True)
    except FlamesCourse.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Course not found or not active.'})

    try:
        # Scope referral code lookup to the course's edition; fall back to global lookup
        referral_qs = ReferralCode.objects.filter(code=code, is_active=True)
        if course.edition_id:
            referral_qs = referral_qs.filter(
                Q(edition=course.edition) | Q(edition__isnull=True)
            )
        referral = referral_qs.first()
        if not referral:
            raise ReferralCode.DoesNotExist
    except ReferralCode.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invalid referral code.'})

    if registration_mode == 'TEAM' and referral.referral_type != 'TEAM':
        return JsonResponse({'status': 'error', 'message': 'This code can only be used for solo registrations.'})

    if registration_mode == 'SOLO' and referral.referral_type != 'ALUMNI':
        return JsonResponse({'status': 'error', 'message': 'This code can only be used for team registrations.'})

    if referral.expires_at and referral.expires_at < timezone.now():
        return JsonResponse({'status': 'error', 'message': 'This referral code has expired.'})

    discounted_price = max(0, int(course.discount_price) - referral.discount_amount)
    return JsonResponse({
        'status': 'success',
        'message': 'Valid referral code.',
        'original_price':    int(course.discount_price),   # base (real) price
        'discounted_price':  discounted_price,              # after referral deduction
        'discount_amount':   referral.discount_amount,
    })

# ============================= NEW FLAMES REGISTRATION PAGE ==========================

def _get_active_edition():
    """Helper: return the currently active FlamesEdition, or None."""
    try:
        return FlamesEdition.objects.get(is_active=True)
    except FlamesEdition.DoesNotExist:
        return None


@ratelimit(key='ip', rate='8/m', method=['POST'], block=False)
def register_flames(request, slug):
    course = get_object_or_404(FlamesCourse, slug=slug, is_active=True)
    # Use the course's own edition as the authoritative edition for this registration.
    # This ensures FLAMES 26 submissions are always scoped to the correct edition
    # regardless of which edition the admin marked as globally "active".
    active_edition = course.edition  # never None — FK is required on FlamesCourse

    # If user is logged in, check duplicate + limit BEFORE showing GET form
    if request.user.is_authenticated and request.user.role == 'student':
        base_qs = FlamesRegistration.objects.filter(
            user=request.user,
            edition=active_edition,
        ).exclude(status='Rejected') if active_edition else FlamesRegistration.objects.none()

        if base_qs.filter(course=course).exists():
            messages.warning(request, f"You have already registered for {course.title}.")
            # Redirect to the edition-appropriate dashboard
            if active_edition and active_edition.year == 2026:
                return redirect('student_flames26')
            return redirect('student_flames')

    if request.method == 'POST':
        if getattr(request, 'limited', False):
            messages.error(request, 'Too many registration attempts. Please wait a minute and try again.')
            if active_edition and active_edition.year == 2026:
                return redirect('flames26_register', track_slug=course.slug)
            return redirect('flames_register', slug=course.slug)

        # ── Guard: registrations must be open ─────────────────────────
        if not active_edition.registration_open:
            messages.error(request, "Registrations for this edition are currently closed.")
            if active_edition.year == 2026:
                return redirect('flames26_register', track_slug=course.slug)
            return redirect('flames_register', slug=course.slug)

        # ── Form data ─────────────────────────────────────────────────
        full_name         = (request.POST.get('full_name') or '').strip()
        email             = (request.POST.get('email') or '').strip().lower()
        contact_number    = request.POST.get('contact_number', '').strip()
        college           = (request.POST.get('college') or '').strip()
        year              = (request.POST.get('year') or '').strip()       # academic year ("2nd Year" etc.)
        message           = (request.POST.get('message') or '').strip()
        registration_mode = (request.POST.get('registration_mode') or 'SOLO').strip().upper()
        referral_code_text = (request.POST.get('referral_code') or '').strip()

        # ── Validate referral code ─────────────────────────────────────
        is_f26 = active_edition and active_edition.year == 2026

        def render_error(msg):
            """Re-render the correct registration page on validation errors."""
            messages.error(request, msg)
            if is_f26:
                return redirect('flames26_register', track_slug=course.slug)
            return render(request, "home/flames_register.html", {
                'course': course, 'user': request.user,
                'edition': active_edition, 'colleges': [
                    "GLA University, Mathura",
                    "Lovely Professional University, Jalandhar",
                    "Shiv Nadar University, Greater Noida",
                    "Delhi Technological University, Delhi",
                    "Acharya Narendra Dev College, Delhi",
                    "LDRP Institute of Technology and Research, Gandhinagar",
                    "BSA College of Engineering, Mathura",
                    "Other"
                ]
            })

        if not full_name:
            return render_error('Full name is required.')

        if not email:
            return render_error('Email is required.')

        try:
            validate_email(email)
        except ValidationError:
            return render_error('Please enter a valid email address.')

        if not college:
            return render_error('College is required.')

        if not year:
            return render_error('Year of study is required.')

        if registration_mode not in ('SOLO', 'TEAM'):
            return render_error('Invalid registration mode selected.')

        if not contact_number.isdigit() or len(contact_number) != 10:
            return render_error('Contact number must contain exactly 10 digits.')

        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name  = name_parts[1] if len(name_parts) > 1 else ''

        referral_code = None
        if referral_code_text:
            try:
                referral_qs = ReferralCode.objects.filter(code=referral_code_text, is_active=True)
                if active_edition:
                    referral_qs = referral_qs.filter(
                        Q(edition=active_edition) | Q(edition__isnull=True)
                    )
                referral_code = referral_qs.get()

                if registration_mode == 'TEAM' and referral_code.referral_type != 'TEAM':
                    return render_error('Invalid referral code for team registration.')

                if registration_mode == 'SOLO' and referral_code.referral_type != 'ALUMNI':
                    return render_error('Invalid referral code for solo registration.')

                if referral_code.expires_at and referral_code.expires_at < timezone.now():
                    return render_error('This referral code has expired.')

            except ReferralCode.DoesNotExist:
                return render_error('Invalid referral code.')

        # ── Atomic transaction: resolve/create user + register ─────────
        with transaction.atomic():

            # ─ Resolve student account ────────────────────────────────
            student = None
            user_exists = CustomUser.objects.filter(email=email).exists()

            if request.user.is_authenticated and request.user.role == 'student':
                student = request.user
            elif user_exists:
                student = CustomUser.objects.get(email=email)
            else:
                username = request.POST.get('username') or email.split('@')[0]
                base_username = username
                counter = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                student = CustomUser.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    mobile_number=contact_number,
                    college=college,
                    is_active=True
                )
                password = request.POST.get('password')
                if password:
                    student.set_password(password)
                else:
                    student.set_password(CustomUser.objects.make_random_password())
                student.save()

            # ─ Race-condition-safe: lock all registrations for this user+edition ─
            if active_edition:
                locked_regs = FlamesRegistration.objects.select_for_update().filter(
                    user=student,
                    edition=active_edition,
                ).exclude(status='Rejected')

                if locked_regs.count() >= FlamesRegistration.MAX_COURSES_PER_EDITION:
                    return render_error(
                        f"You have already registered for "
                        f"{FlamesRegistration.MAX_COURSES_PER_EDITION} courses this edition."
                    )

                if locked_regs.filter(course=course).exists():
                    messages.warning(request, f"You have already registered for {course.title}.")
                    if active_edition and active_edition.year == 2026:
                        return redirect('student_flames26')
                    return redirect('student_flames')

            # ─ Create registration ────────────────────────────────────
            registration = FlamesRegistration(
                user=student,
                course=course,
                edition=active_edition,   # ← edition wired here
                year=year,                # student's academic year
                message=message,
                registration_mode=registration_mode,
                referral_code=referral_code
            )
            registration.save()

            # ─ Team registration ──────────────────────────────────────
            if registration_mode == 'TEAM':
                member_students = []
                team_member_emails = []
                for i in range(1, 5):
                    member_email = (request.POST.get(f'team_member_email_{i}') or '').strip().lower()
                    if not member_email:
                        return render_error(f'Teammate {i + 1} email is required for team registration.')
                    team_member_emails.append(member_email)

                if len(set(team_member_emails)) != 4:
                    return render_error('All teammate emails must be unique.')

                leader_email = (student.email or email).strip().lower()
                if leader_email in team_member_emails:
                    return render_error('You cannot add yourself as a teammate.')

                for member_email in team_member_emails:
                    member_student = CustomUser.objects.filter(email__iexact=member_email).first()
                    if not member_student:
                        return render_error(f"User with email '{member_email}' does not exist.")

                    already_direct = FlamesRegistration.objects.filter(
                        user=member_student,
                        course=course,
                    ).exclude(status='Rejected').exists()

                    already_team = FlamesTeamMember.objects.filter(
                        member=member_student,
                        team__course=course,
                    ).exists()

                    if already_direct or already_team:
                        return render_error(
                            f"{member_email} is already registered for this course."
                        )

                    member_students.append(member_student)

                team_name = request.POST.get('team_name') or f"Team {first_name}"

                team = FlamesTeam.objects.create(
                    name=team_name,
                    team_leader=student,
                    course=course,
                    edition=active_edition,   # ← edition wired here too
                )

                registration.team = team
                registration.save()

                FlamesTeamMember.objects.create(team=team, member=student, is_leader=True)

                for member_student in member_students:
                    FlamesTeamMember.objects.create(
                        team=team, member=member_student, is_leader=False
                    )

                messages.success(request, f"Team '{team_name}' registered for {course.title}!")
            else:
                messages.success(request, f"You have been registered for {course.title} successfully!")

            if not request.user.is_authenticated:
                login(request, student)
                messages.info(request, "You have been automatically logged into your student account.")

            # Redirect to the edition-appropriate student dashboard
            if active_edition and active_edition.year == 2026:
                return redirect('student_flames26')
            return redirect('student_flames')

    colleges = [
        "GLA University, Mathura",
        "Lovely Professional University, Jalandhar",
        "Shiv Nadar University, Greater Noida",
        "Delhi Technological University, Delhi",
        "Acharya Narendra Dev College, Delhi",
        "LDRP Institute of Technology and Research, Gandhinagar",
        "BSA College of Engineering, Mathura",
        "Other"
    ]

    return render(request, "home/flames_register.html", {
        'course': course,
        'edition': active_edition,
        'user': request.user if request.user.is_authenticated else None,
        'colleges': colleges,
    })

# ============================ FLAMES 26 PAGE ==========================

def flames26(request):
    try:
        edition_2026 = FlamesEdition.objects.get(year=2026)
        courses = FlamesCourse.objects.filter(edition=edition_2026, is_active=True)
    except FlamesEdition.DoesNotExist:
        edition_2026 = None
        courses = FlamesCourse.objects.none()
    return render(request, "home/flames26/flames26.html", {
        'courses': courses,
        'edition': edition_2026,
    })


def flames26_track_detail(request, track_slug):
    """
    Course detail page for a FLAMES 26 track — driven entirely by the database.
    """
    from django.http import Http404

    try:
        edition_2026 = FlamesEdition.objects.get(year=2026)
        course = FlamesCourse.objects.filter(
            slug=track_slug, edition=edition_2026, is_active=True
        ).first()
    except FlamesEdition.DoesNotExist:
        course = FlamesCourse.objects.filter(slug=track_slug, is_active=True).first()

    if not course:
        raise Http404("Course not found")

    return render(request, "home/flames26/track_detail.html", {
        "course": course,
    })


# ============================ FLAMES 26 REGISTRATION PAGE ==========================

def flames26_register(request, track_slug):
    """
    Registration page for a specific FLAMES '26 track.
    Requires login — unauthenticated users are redirected to the login page
    with ?next= so they bounce back here automatically after signing in.
    Submission is handled by the existing register_flames view.
    """
    from django.http import Http404
    from django.urls import reverse

    # ── Auth gate ─────────────────────────────────────────────────────
    if not request.user.is_authenticated:
        messages.info(
            request,
            "🔑 Please sign in or create an account to register for FLAMES '26 — "
            "your details will be pre-filled automatically after login."
        )
        login_url = reverse('login') + '?next=' + request.get_full_path()
        return redirect(login_url)

    # Require the 2026 edition to exist
    try:
        edition_2026 = FlamesEdition.objects.get(year=2026)
    except FlamesEdition.DoesNotExist:
        raise Http404("FLAMES 2026 edition has not been set up yet.")

    # Hard 404 if the slug doesn't match an active DB course in that edition
    course = get_object_or_404(
        FlamesCourse,
        slug=track_slug,
        edition=edition_2026,
        is_active=True,
    )

    active_edition = _get_active_edition()

    # ── Duplicate-registration guard ──────────────────────────────────────────
    if active_edition:
        already = FlamesRegistration.objects.filter(
            user=request.user,
            course=course,
            edition=active_edition,
        ).exclude(status='Rejected').exists()
        if already:
            messages.warning(request, f"You are already registered for {course.title}.")
            return redirect('student_flames26')

    colleges = [
        "GLA University, Mathura",
        "Lovely Professional University, Jalandhar",
        "Shiv Nadar University, Greater Noida",
        "Delhi Technological University, Delhi",
        "Acharya Narendra Dev College, Delhi",
        "LDRP Institute of Technology and Research, Gandhinagar",
        "BSA College of Engineering, Mathura",
        "Other",
    ]

    # ── Pre-fill from the logged-in user's profile ────────────────────────────
    u = request.user
    prefill = {
        'full_name':      f"{u.first_name} {u.last_name}".strip(),
        'email':          u.email,
        'contact_number': u.mobile_number or '',
        'college':        u.college or '',
        'username':       u.username,
    }

    return render(request, "home/flames26/flames26_register.html", {
        "course":   course,
        "edition":  active_edition,
        "colleges": colleges,
        "prefill":  prefill,
    })
