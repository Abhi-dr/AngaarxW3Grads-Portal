from django.contrib.auth import get_user_model
from accounts.models import Student
from practice.models import Streak

def student_context_processor(request):
    student = None
    if request.user.is_authenticated:
        User = get_user_model()
        try:
            student = request.user.student
        except Student.DoesNotExist:
            pass
    return {'student': student}

def streak_context(request):
    if request.user.is_authenticated:  # Ensure the user is logged in
        if hasattr(request.user, 'student'):  # Check if the user has a related 'Student' instance
            streak = Streak.objects.filter(user=request.user.student).first()
            return {'streak': streak}
    return {'streak': None}  # Return None if the user is not logged in or does not have a 'Student' instance

