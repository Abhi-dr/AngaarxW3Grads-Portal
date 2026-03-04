from accounts.models import CustomUser
from practice.models import Streak
from home.models import Alumni, ReferralCode


def user_context_processor(request):
    """
    Injects `user_type` and `user` into every template context.

    WHY THIS CHANGED (Phase 1 migration):
    Before:  request.user was auth.User, and Student/Instructor/Administrator were
             separate tables with a OneToOne back to auth.User.
             So `hasattr(request.user, 'student')` checked if a Student row existed.

    After:   request.user is now CustomUser directly — it HAS all the fields
             (role, mobile_number, dob etc) built-in. There's no separate 'student'
             reverse-accessor anymore.
             We now read `request.user.role` to determine the type.
    """

    if request.path.startswith('/tera0mera1_dknaman/'):
        return {}

    user_type = None
    user_object = None

    if request.user.is_authenticated:
        # request.user IS the CustomUser — it has .role, .coins, .dob, etc. directly
        user_type   = request.user.role    # 'student' | 'instructor' | 'admin'
        user_object = request.user         # same object, all fields available

    return {
        'user_type': user_type,
        'user':      user_object,
    }


def streak_context(request):
    """
    Injects `streak`, `can_restore_streak`, `solved_today` for students.

    WHY THIS CHANGED:
    Old code: `if hasattr(request.user, 'student')` + `request.user.student`
              → student was a separate model instance.
    New code: `request.user.role == 'student'` + pass `request.user` directly
              → CustomUser has all fields, Streak FK points to CustomUser.
    """
    context = {}
    if request.user.is_authenticated and request.user.role == 'student':
        # Streak.get_user_streak() expects a CustomUser (the FK was rewired in Phase 1)
        streak = Streak.get_user_streak(request.user)
        context['streak']              = streak
        context['can_restore_streak']  = streak.can_restore_streak()
        context['solved_today']        = streak.has_solved_today()
    return context
