from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as message
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Article, Comment

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
        "articles": articles,
        "user": request.user
    }
    
    return render(request, "home/articles.html", parameters)

# ==================== ARTICLE ============================

def article(request, slug):
    article = Article.objects.get(slug=slug)
    comments = Comment.objects.filter(article=article)
    
    # Show only preview (first 5 lines) if user is not logged in
    if not request.user.is_authenticated:
        content_lines = article.content.split("\n")[:25]  # Get first 5 lines
        preview_content = "\n".join(content_lines) + "<p>...</p>"
    else:
        preview_content = article.content  # Show full content if logged in

    return render(request, "home/article.html", {
        "article": article,
        "preview_content": preview_content,
        "comments": comments,
        "user": request.user
    })

# ==================== LIKE ARTICLE ============================

@login_required
def like_article(request):
    if request.method == 'POST':
        article_id = request.POST.get('article_id')
        article = get_object_or_404(Article, id=article_id)
        
        if request.user in article.likes.all():
            article.likes.remove(request.user)
            liked = False
        else:
            article.likes.add(request.user)
            liked = True
            
        return JsonResponse({
            'liked': liked,
            'total_likes': article.total_likes()
        })

# ==================== POST COMMENT ============================

@login_required
def post_comment(request, article_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        article = get_object_or_404(Article, id=article_id)
        content = request.POST.get('content')
        
        if content:
            comment = Comment.objects.create(
                article=article,
                user=request.user,
                content=content
            )
            
            return JsonResponse({
                'status': 'success',
                'comment': {
                    'author': comment.user.username,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime("%B %d, %Y"),
                    'author_initial': comment.user.username[0],
                },
                'total_comments': article.comments.count()
            })
            
    return JsonResponse({'status': 'error'}, status=400)

# =======================================================================================
# ==================================== ACHIEVERS ========================================
# =======================================================================================

from administration.models import Achievement

def our_achievers(request):
    return render(request, 'home/achievers.html')

def fetch_achievers_data(request):
    achievers = Achievement.objects.all().order_by('-date')
    data = []
    for achiever in achievers:
        data.append({
            'name': achiever.student.first_name + ' ' + achiever.student.last_name,
            'profile_pic': achiever.student.profile_pic.url,
            "linkedin": achiever.student.linkedin_id,
            "github": achiever.student.github_id,
            'title': achiever.title,
            'description': achiever.description,
            "achievement_type": achiever.achievement_type,
            'date': achiever.date.strftime('%Y-%m-%d'),
        })
    return JsonResponse(data, safe=False)



