from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("our-team/", views.our_team, name="our_team"),
    
    path("flames/", views.flames, name="flames"),
    
    
    path("articles/", views.articles, name="articles"),
    path("article/<slug:slug>/", views.article, name="article"),
    path("like-article/", views.like_article, name="like_article"),
    path("post-comment/<int:article_id>/", views.post_comment, name="post_comment"),
    
    path("our_achievers/", views.our_achievers, name="our_achievers"),
    path('fetch_achievers_data/', views.fetch_achievers_data, name='fetch_achievers_data'),
    path('fetch_top_performers/', views.fetch_top_performers, name='fetch_top_performers'),
    
]
