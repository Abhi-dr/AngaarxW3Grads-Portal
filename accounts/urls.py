from django.urls import path, include
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),
    
    path('check_username_availability/', views.check_username_availability, name='check_username_availability'),
    path('check_username_exists/', views.check_username_exists, name='check_username_exists'),
    path('check_email_availability/', views.check_email_availability, name='check_email_availability'),
    
    path("block_student/<int:id>/", views.block_student, name="block_student"),
    path("unblock_student/<int:id>/", views.unblock_student, name="unblock_student"),
    
    path("get_active_sheet_timer/", views.get_active_sheet_timer, name="get_active_sheet_timer"),
    
    path('request-password-reset/', views.request_password_reset, name='request_password_reset'),
    path('reset-password/<int:user_id>/<str:token>/', views.reset_password, name='reset_password'),
    
    # API Endpoints
    path('api/students', views.get_students_api, name='get_students_api'),

    # Social authentication URLs (includes Google OAuth)
    path('social/', include('allauth.urls')),
]
