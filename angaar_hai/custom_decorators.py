from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser


def admin_required(view_func):
    """
    Decorator that checks if the logged-in user has role='admin'.

    WHY CHANGED: Previously used `Administrator` proxy model to check admin status.
    Now CustomUser has a `role` field directly — so we just check request.user.role == 'admin'.
    No separate table lookup needed.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            if request.user.is_authenticated and request.user.role == 'admin':
                return view_func(request, *args, **kwargs)
            return render(request, "error.html", {"error": "403", "message": "Access denied."})
        except Exception as e:
            print(e)
            return render(request, "error.html", {"error": "403", "message": str(e)})

    return _wrapped_view
