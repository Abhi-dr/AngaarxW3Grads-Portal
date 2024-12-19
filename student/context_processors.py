from accounts.models import Student, Instructor, Administrator
from practice.models import Streak

def user_context_processor(request):
    
    if request.path.startswith('/tera0mera1_dknaman/'):
        return {} 
    
    user_type = None
    user_object = None

    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'student'):
                user_type = 'student'
                user_object = request.user.student
            elif hasattr(request.user, 'instructor'):
                user_type = 'instructor'
                user_object = request.user.instructor
            elif hasattr(request.user, 'administrator'):
                user_type = 'administrator'
                user_object = request.user.administrator
        except (Student.DoesNotExist, Instructor.DoesNotExist, Administrator.DoesNotExist):
            pass

    return {
        'user_type': user_type,
        'user': user_object,
    }


def streak_context(request):
    if request.user.is_authenticated:  # Ensure the user is logged in
        if hasattr(request.user, 'student'):  # Check if the user has a related 'Student' instance
            streak = Streak.objects.filter(user=request.user.student).first()
            return {'streak': streak}
    return {'streak': None}  # Return None if the user is not logged in or does not have a 'Student' instance


# def student_context_processor(request):
#     student = None
#     if request.user.is_authenticated:
#         User = get_user_model()
#         try:
#             student = request.user.student
#         except Student.DoesNotExist:
#             pass
#     return {'student': student}

