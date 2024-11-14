from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("flames", views.flames, name="flames"),
    
    path("Angaar++🔥", views.angaar_plus, name="angaar_plus"),
    
    path("scholarship_test", views.scholarship_test, name="scholarship_test"),
]
