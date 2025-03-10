from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import Administrator  # Replace with your app's name

def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        try:
            # Check if the authenticated user is an administrator
            if Administrator.objects.filter(pk=request.user.pk).exists():
                return view_func(request, *args, **kwargs)
        except Exception as e:
            print(e)
            data = {
                "error": "403",
                "message": e
            }
            # logout the current user
            return render(request, "error.html", data)
    
    return _wrapped_view
