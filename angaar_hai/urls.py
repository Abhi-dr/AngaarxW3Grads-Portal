from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
import administration.problem_views

import debug_toolbar


urlpatterns = [
    path('tera0mera1_dknaman/', admin.site.urls),
    path("", include("home.urls")),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("student.urls")),
    
    path("practice/", include("practice.urls")),
    
    path("instructor/", include("instructor.urls")),
    path("administration/", include("administration.urls")), 
    path("judge0/callback", administration.problem_views.judge0_callback, name="judge0_callback"),
    
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('', include('django_prometheus.urls')),
   
    
    path('__debug__/', include(debug_toolbar.urls)),

    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# handle 404
 
handler404 = "accounts.views.page_not_found_view"
