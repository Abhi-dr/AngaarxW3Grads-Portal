from django.contrib.auth import get_user_model
from accounts.models import Student

def student_context_processor(request):
    student = None
    if request.user.is_authenticated:
        User = get_user_model()
        try:
            student = request.user.student
        except Student.DoesNotExist:
            pass
    return {'student': student}
