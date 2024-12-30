from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),
    
    path('check_username_availability/', views.check_username_availability, name='check_username_availability'),    
    
    path("block_student/<int:id>/", views.block_student, name="block_student"),
    path("unblock_student/<int:id>/", views.unblock_student, name="unblock_student"),
    
    path("get_active_sheet_timer/", views.get_active_sheet_timer, name="get_active_sheet_timer"),
    
    path('request-password-reset/', views.request_password_reset, name='request_password_reset'),
    path('reset-password/<int:user_id>/<str:token>/', views.reset_password, name='reset_password'),
    
]   
