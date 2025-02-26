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
    
    # Show only preview (first 5 lines) if user is not logged in
    if not request.user.is_authenticated:
        content_lines = article.content.split("\n")[:25]  # Get first 5 lines
        preview_content = "\n".join(content_lines) + "<p>...</p>"
    else:
        preview_content = article.content  # Show full content if logged in

    return render(request, "home/article.html", {
        "article": article,
        "preview_content": preview_content
    })
    

