from django.shortcuts import render
from .models import SiteSettings

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow superusers and staff to bypass maintenance
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        # Always allow admin page access
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        try:
            settings = SiteSettings.get_instance()
            if settings.maintenance_mode:
                return render(request, 'maintenance.html', status=503)
        except:
            pass  # Fallback if DB isn't ready

        return self.get_response(request)
