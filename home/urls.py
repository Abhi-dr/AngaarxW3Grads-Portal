from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("our-team/", views.our_team, name="our_team"),
    path("articles/", views.articles, name="articles"),
    path("article/<slug:slug>/", views.article, name="article"),
    path("like-article/", views.like_article, name="like_article"),
    path("post-comment/<int:article_id>/", views.post_comment, name="post_comment"),
]
