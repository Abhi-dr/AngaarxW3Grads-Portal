from django.shortcuts import render, redirect
from django.contrib import messages as message
from .models import Article

def home(request):
    return render(request, "home/index.html")

def about(request):
    return render(request, "home/about.html")

def our_team(request):
    return render(request, "home/team.html")

# ======================== ARTICLES ========================

def articles(request):
    
    articles = Article.objects.all().order_by("-created_at")
    
    parameters = {
        "articles": articles
    }
    
    return render(request, "home/articles.html", parameters)

# ==================== ARTICLE ============================

def article(request, slug):
    
    article = Article.objects.get(slug=slug)
    
    parameters = {
        "article": article
    }
    
    return render(request, "home/article.html", parameters)

