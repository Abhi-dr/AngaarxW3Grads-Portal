from django.shortcuts import render, redirect, HttpResponse
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
    

# ======================================== QUERY ==================================

from django.core.mail import EmailMultiAlternatives, get_connection
from dotenv import load_dotenv
import os

load_dotenv()

def query(user_email, user_query):
    subject = 'New User Query Received'
    from_email = user_email
    to_email = ['sgnmiu@gmail.com']
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
        <div style="background-color: #f4f4f4; padding: 20px; text-align: center;">
        <h2 style="color: #2C3E50;">New User Query</h2>
        <p style="font-size: 16px; color: #555555;"><strong>Email:</strong> {user_email}</p>
        <p style="font-size: 16px; color: #555555;"><strong>Query:</strong> {user_query}</p>
        <p style="font-size: 14px; color: #777777; margin-top: 30px;">Please respond to the user as soon as possible.</p>
        </div>
    </body>
    </html>
    """

     # Use Gmail SMTP connection
    gmail_connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host='smtp.gmail.com',
        port=587,
        username="sgnmiu@gmail.com",
        password=os.getenv("EMAIL_HOST_PASSWORD"),  
        use_tls=True,
    )

    email = EmailMultiAlternatives(subject, '', from_email, to_email, reply_to=[user_email], connection=gmail_connection)
    email.attach_alternative(html_content, 'text/html')
    email.send()
    
    print(f"\nQUERY EMAIL SENT! from {user_email} to {to_email} \n")


# ======================== SEND QUERY ========================

def send_query(request):
    if request.method == "POST":
        user_email = request.POST.get('email')
        user_query = request.POST.get('query')

        if user_email and user_query:
            query(user_email, user_query)
            message.success(request, "Query Sent Successfully!")
            return redirect("home")

    return HttpResponse("Failed to Send Query", status=400)


