from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from home.models import Article
from practice.models import POD, Submission, Question, Sheet, Batch,EnrollmentRequest
from django.db.models import Subquery, OuterRef
from django.core.cache import cache
from django.utils import timezone

import datetime

# ============================== ALL ARTICLES ==============================

@login_required(login_url='login')
@staff_member_required
def articles(request):    
    return render(request, 'administration/articles/articles.html')

def fetch_all_articles(request):   
    
    articles = Article.objects.all().order_by('-id')

    data = [
        {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "thumbnail": article.thumbnail.url,
            "likes_count": article.total_likes(),
            "comments_count": article.comments.count(),
        } for article in articles
    ]
    
    # Store data in cache

    return JsonResponse({'data': data})


# ============================== ARTICLE ==============================

@login_required(login_url='login')
@staff_member_required
def article(request, slug):
    
    article = get_object_or_404(Article, slug=slug)
    comments = article.comments.select_related('user').order_by('-created_at')
    
    return render(request, 'administration/articles/article.html', {
        'article': article,
        'comments': comments,
    })

# ============================== ADD ARTICLE ==============================

@login_required(login_url='login')
@staff_member_required
def add_article(request):
    
    if request.method == 'POST':
        
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        thumbnail = request.FILES.get('thumbnail')
        
        article = Article.objects.create(
            title = title,
            content = content,
            thumbnail = thumbnail
        )
        
        messages.success(request, 'Article added successfully')
        
        cache.delete('fetch_all_articles')
        
        return redirect('administrator_articles')
    
    return render(request, 'administration/articles/add_article.html')

# ============================== DELETE ARTICLE ==============================

@login_required(login_url='login')
@staff_member_required
def delete_article(request, id):
    
    article = get_object_or_404(Article, id=id)
    article.delete()
    messages.success(request, 'Article deleted successfully')
    
    cache.delete('fetch_all_articles')
    
    return redirect('administrator_articles')

# ============================== EDIT ARTICLE ==============================
@login_required(login_url='login')
@staff_member_required
def edit_article(request, id):
    
    article = get_object_or_404(Article, id=id)
    
    if request.method == 'POST':
        
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        thumbnail = request.FILES.get('thumbnail')
        
        article.title = title
        article.content = content
        
        if thumbnail:
            article.thumbnail = thumbnail
        
        article.save()
        
        messages.success(request, 'Article updated successfully')
        
        cache.delete('fetch_all_articles')
        
        return redirect('administrator_articles')
    
    return render(request, 'administration/articles/edit_article.html', {'article': article})
