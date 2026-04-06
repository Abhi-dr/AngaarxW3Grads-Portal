import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST

from home.models import (
    FlamesCourse, FlamesEdition, FlamesRegistration,
    FlamesTeam, FlamesTeamMember, ReferralCode,
)


# ══════════════════════════════════════════════════════════════════════════════
# FLAMES 26 STUDENT DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@login_required(login_url='login')
def student_flames26(request):
    """
    Student-panel dashboard for FLAMES 2026.

    Section A — courses the student has already registered for.
    Section B — active FLAMES 26 courses the student has NOT registered for yet.
    """
    # Resolve the 2026 edition (may not exist yet)
    try:
        edition_2026 = FlamesEdition.objects.get(year=2026)
    except FlamesEdition.DoesNotExist:
        edition_2026 = None

    registered_registrations = []
    registered_course_ids = set()
    available_courses = []
    registration_open = False

    if edition_2026:
        registration_open = edition_2026.registration_open

        # Section A — registered (non-rejected) courses for this user in the 2026 edition
        registered_registrations = list(
            FlamesRegistration.objects.filter(
                user=request.user,
                edition=edition_2026,
            )
            .exclude(status='Rejected')
            .select_related('course', 'team')
            .order_by('-created_at')
        )
        registered_course_ids = {r.course_id for r in registered_registrations}

        # Section B — active 2026 courses NOT yet registered
        available_courses = list(
            FlamesCourse.objects.filter(edition=edition_2026, is_active=True)
            .exclude(id__in=registered_course_ids)
        )
        for course in available_courses:
            course.savings_amount = max(course.price - course.discount_price, 0)

    # Max registrations cap for display
    max_courses = FlamesRegistration.MAX_COURSES_PER_EDITION
    at_limit = len(registered_registrations) >= max_courses

    return render(request, 'student/flames/flames26_dashboard.html', {
        'edition':                 edition_2026,
        'registered_registrations': registered_registrations,
        'available_courses':        available_courses,
        'registration_open':        registration_open,
        'at_limit':                 at_limit,
        'max_courses':              max_courses,
        'active_tab':              'flames26',
    })


# ══════════════════════════════════════════════════════════════════════════════
# AJAX — INLINE SOLO REGISTRATION FROM STUDENT DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@login_required(login_url='login')
@require_POST
def ajax_flames26_register(request):
    """
    Handles inline SOLO registration for FLAMES 26 from the student dashboard.
    Returns JSON — the frontend swaps the course card without a full page reload.

    POST body (form-encoded):
        course_id       int     required
        year            str     required   ("1st Year", "2nd Year", …)
        message         str     optional
        referral_code   str     optional
    """
    def err(msg, status=400):
        return JsonResponse({'status': 'error', 'message': msg}, status=status)

    # ── Resolve edition ────────────────────────────────────────────────────
    try:
        edition_2026 = FlamesEdition.objects.get(year=2026)
    except FlamesEdition.DoesNotExist:
        return err("FLAMES 2026 edition has not been set up yet.", 404)

    if not edition_2026.registration_open:
        return err("Registrations for FLAMES 2026 are currently closed.")

    # ── Resolve course ─────────────────────────────────────────────────────
    course_id = request.POST.get('course_id', '').strip()
    if not course_id:
        return err("course_id is required.")

    course = FlamesCourse.objects.filter(
        id=course_id, edition=edition_2026, is_active=True
    ).first()
    if not course:
        return err("Course not found or not active.")

    year    = request.POST.get('year', '').strip()
    message = request.POST.get('message', '').strip()

    if not year:
        return err("Please select your year of study.")

    with transaction.atomic():
        # ── Race-condition-safe duplicate + limit check ────────────────────
        locked_regs = FlamesRegistration.objects.select_for_update().filter(
            user=request.user,
            edition=edition_2026,
        ).exclude(status='Rejected')

        if locked_regs.filter(course=course).exists():
            return err(f"You are already registered for {course.title}.")

        if locked_regs.count() >= FlamesRegistration.MAX_COURSES_PER_EDITION:
            return err(
                f"You have already registered for the maximum of "
                f"{FlamesRegistration.MAX_COURSES_PER_EDITION} courses this edition."
            )

        # ── Referral code ──────────────────────────────────────────────────
        referral_code = None
        referral_code_text = request.POST.get('referral_code', '').strip()
        if referral_code_text:
            from django.db.models import Q
            from django.utils import timezone
            referral_qs = ReferralCode.objects.filter(
                code=referral_code_text,
                is_active=True,
                referral_type='ALUMNI',   # solo registrations use ALUMNI codes
            ).filter(
                Q(edition=edition_2026) | Q(edition__isnull=True)
            )
            referral_code = referral_qs.first()
            if referral_code_text and not referral_code:
                return err("Invalid referral code.")
            if referral_code and referral_code.expires_at and referral_code.expires_at < timezone.now():
                return err("This referral code has expired.")

        # ── Create registration ────────────────────────────────────────────
        registration = FlamesRegistration(
            user=request.user,
            course=course,
            edition=edition_2026,
            year=year,
            message=message,
            registration_mode='SOLO',
            referral_code=referral_code,
        )
        registration.save()

    return JsonResponse({
        'status':  'success',
        'message': f"Successfully registered for {course.title}! 🎉",
        'registration': {
            'id':              registration.id,
            'course_title':    course.title,
            'course_subtitle': course.subtitle,
            'course_slug':     course.slug,
            'icon_class':      course.icon_class,
            'icon_color':      course.icon_color,
            'level':           course.level,
            'status':          registration.status,
            'payable_amount':  registration.payable_amount,
            'created_at':      registration.created_at.strftime('%b %d, %Y'),
        }
    })
