from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as message
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Article, Comment, FlamesCourse, FlamesCourseTestimonial, FlamesRegistration
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count
from practice.models import Batch, Submission, Question
from django.contrib import messages
import requests
import time
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


from administration.models import Achievement

def flare(request):
    return render(request, 'home/flare.html')