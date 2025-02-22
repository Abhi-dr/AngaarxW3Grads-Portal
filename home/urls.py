from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("our_team/", views.our_team, name="our_team"),
    
    path("job-articles/", views.articles, name="articles"),
    path("article/<slug:slug>/", views.article, name="article"),
    
]
