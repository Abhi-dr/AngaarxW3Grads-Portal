from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import FlamesCourse, FlamesCourseTestimonial, FlamesRegistration, ReferralCode, FlamesTeam, FlamesTeamMember, FlamesEdition
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db import transaction
from accounts.models import CustomUser

# ===================================== FLAMES PAGE ==============================

def flames(request):
    try:
        active_edition = FlamesEdition.objects.get(is_active=True)
        courses = FlamesCourse.objects.filter(edition=active_edition, is_active=True)
    except FlamesEdition.DoesNotExist:
        # Fallback: show all active courses if no edition is set as active
        active_edition = None
        courses = FlamesCourse.objects.filter(is_active=True)
    return render(request, "home/flames.html", {
        'courses': courses,
        'edition': active_edition,
    })

# =================================== PROGRAM DETAILS ============================

def course_detail(request, slug):
    course = get_object_or_404(FlamesCourse, slug=slug, is_active=True)
    testimonials = FlamesCourseTestimonial.objects.filter(course=course)
    
    context = {
        'course': course,
        'testimonials': testimonials,
        'learning_points': course.get_learning_points(),
    }
    
    return render(request, "home/course_detail.html", context)


# ============================= VALIDATE REFERRAL CODE ==========================

def validate_referral(request):
    """Validate referral code and return price details."""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

    code              = request.GET.get('code', '')
    course_id         = request.GET.get('course_id', '')
    registration_mode = request.GET.get('registration_mode', '')

    if not code or not course_id:
        return JsonResponse({'status': 'error', 'message': 'Missing required parameters.'}, status=400)

    try:
        course = FlamesCourse.objects.get(id=course_id, is_active=True)
    except FlamesCourse.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Course not found or not active.'})

    try:
        # Scope referral code lookup to the course's edition; fall back to global lookup
        referral_qs = ReferralCode.objects.filter(code=code, is_active=True)
        if course.edition_id:
            referral_qs = referral_qs.filter(
                Q(edition=course.edition) | Q(edition__isnull=True)
            )
        referral = referral_qs.first()
        if not referral:
            raise ReferralCode.DoesNotExist
    except ReferralCode.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invalid referral code.'})

    if registration_mode == 'TEAM' and referral.referral_type != 'TEAM':
        return JsonResponse({'status': 'error', 'message': 'This code can only be used for solo registrations.'})

    if registration_mode == 'SOLO' and referral.referral_type != 'ALUMNI':
        return JsonResponse({'status': 'error', 'message': 'This code can only be used for team registrations.'})

    if referral.expires_at and referral.expires_at < timezone.now():
        return JsonResponse({'status': 'error', 'message': 'This referral code has expired.'})

    discounted_price = max(0, course.price - referral.discount_amount)
    return JsonResponse({
        'status': 'success',
        'message': 'Valid referral code.',
        'original_price':    course.price,
        'discounted_price':  discounted_price,
        'discount_amount':   referral.discount_amount,
    })

# ============================= NEW FLAMES REGISTRATION PAGE ==========================

def _get_active_edition():
    """Helper: return the currently active FlamesEdition, or None."""
    try:
        return FlamesEdition.objects.get(is_active=True)
    except FlamesEdition.DoesNotExist:
        return None


def register_flames(request, slug):
    course = get_object_or_404(FlamesCourse, slug=slug, is_active=True)
    active_edition = _get_active_edition()

    # If user is logged in, check duplicate + limit BEFORE showing GET form
    if request.user.is_authenticated and request.user.role == 'student':
        base_qs = FlamesRegistration.objects.filter(
            user=request.user,
            edition=active_edition,
        ).exclude(status='Rejected') if active_edition else FlamesRegistration.objects.none()

        if base_qs.filter(course=course).exists():
            messages.warning(request, f"You have already registered for {course.title}.")
            return redirect('student_flames')

    if request.method == 'POST':
        # ── Form data ─────────────────────────────────────────────────
        full_name         = request.POST.get('full_name')
        email             = request.POST.get('email').lower()
        contact_number    = request.POST.get('contact_number')
        college           = request.POST.get('college', '')
        year              = request.POST.get('year')        # academic year ("2nd Year" etc.)
        message           = request.POST.get('message', '')
        registration_mode = request.POST.get('registration_mode', 'SOLO')
        referral_code_text = request.POST.get('referral_code', '')

        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name  = name_parts[1] if len(name_parts) > 1 else ''

        # ── Validate referral code ─────────────────────────────────────
        referral_code = None
        if referral_code_text:
            try:
                referral_qs = ReferralCode.objects.filter(code=referral_code_text, is_active=True)
                if active_edition:
                    referral_qs = referral_qs.filter(
                        Q(edition=active_edition) | Q(edition__isnull=True)
                    )
                referral_code = referral_qs.get()

                if registration_mode == 'TEAM' and referral_code.referral_type != 'TEAM':
                    messages.error(request, 'Invalid referral code for team registration.')
                    return render(request, "home/flames_register.html", {'course': course, 'user': request.user})

                if registration_mode == 'SOLO' and referral_code.referral_type != 'ALUMNI':
                    messages.error(request, 'Invalid referral code for solo registration.')
                    return render(request, "home/flames_register.html", {'course': course, 'user': request.user})

                if referral_code.expires_at and referral_code.expires_at < timezone.now():
                    messages.error(request, 'This referral code has expired.')
                    return render(request, "home/flames_register.html", {'course': course, 'user': request.user})

            except ReferralCode.DoesNotExist:
                messages.error(request, 'Invalid referral code.')
                return render(request, "home/flames_register.html", {'course': course, 'user': request.user})

        # ── Atomic transaction: resolve/create user + register ─────────
        with transaction.atomic():

            # ─ Resolve student account ────────────────────────────────
            student = None
            user_exists = CustomUser.objects.filter(email=email).exists()

            if request.user.is_authenticated and request.user.role == 'student':
                student = request.user
            elif user_exists:
                student = CustomUser.objects.get(email=email)
            else:
                username = request.POST.get('username') or email.split('@')[0]
                base_username = username
                counter = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                student = CustomUser.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    mobile_number=contact_number,
                    college=college,
                    is_active=True
                )
                password = request.POST.get('password')
                if password:
                    student.set_password(password)
                else:
                    student.set_password(CustomUser.objects.make_random_password())
                student.save()

            # ─ Race-condition-safe: lock all registrations for this user+edition ─
            if active_edition:
                locked_regs = FlamesRegistration.objects.select_for_update().filter(
                    user=student,
                    edition=active_edition,
                ).exclude(status='Rejected')

                if locked_regs.count() >= FlamesRegistration.MAX_COURSES_PER_EDITION:
                    messages.error(
                        request,
                        f"You have already registered for "
                        f"{FlamesRegistration.MAX_COURSES_PER_EDITION} courses this edition."
                    )
                    return render(request, "home/flames_register.html",
                                  {'course': course, 'user': request.user})

                if locked_regs.filter(course=course).exists():
                    messages.warning(request, f"You have already registered for {course.title}.")
                    return redirect('student_flames')

            # ─ Create registration ────────────────────────────────────
            registration = FlamesRegistration(
                user=student,
                course=course,
                edition=active_edition,   # ← edition wired here
                year=year,                # student's academic year
                message=message,
                registration_mode=registration_mode,
                referral_code=referral_code
            )
            registration.save()

            # ─ Team registration ──────────────────────────────────────
            if registration_mode == 'TEAM':
                team_name = request.POST.get('team_name') or f"Team {first_name}"

                team = FlamesTeam.objects.create(
                    name=team_name,
                    team_leader=student,
                    course=course,
                    edition=active_edition,   # ← edition wired here too
                )

                registration.team = team
                registration.save()

                FlamesTeamMember.objects.create(team=team, member=student, is_leader=True)

                for i in range(1, 5):
                    member_username = request.POST.get(f'team_member_username_{i}')
                    if member_username:
                        try:
                            member_student = CustomUser.objects.get(username=member_username)
                            FlamesTeamMember.objects.create(
                                team=team, member=member_student, is_leader=False
                            )
                        except CustomUser.DoesNotExist:
                            messages.warning(
                                request,
                                f"User '{member_username}' not found and was not added to the team."
                            )

                messages.success(request, f"Team '{team_name}' registered for {course.title}!")
            else:
                messages.success(request, f"You have been registered for {course.title} successfully!")

            if not request.user.is_authenticated:
                login(request, student)
                messages.info(request, "You have been automatically logged into your student account.")

            return redirect('student_flames')

    colleges = [
        "GLA University, Mathura",
        "Lovely Professional University, Jalandhar",
        "Shiv Nadar University, Greater Noida",
        "Delhi Technological University, Delhi",
        "Acharya Narendra Dev College, Delhi",
        "LDRP Institute of Technology and Research, Gandhinagar",
        "BSA College of Engineering, Mathura",
        "Other"
    ]

    return render(request, "home/flames_register.html", {
        'course': course,
        'edition': active_edition,
        'user': request.user if request.user.is_authenticated else None,
        'colleges': colleges,
    })

# ============================ FLAMES 26 PAGE ==========================

def flames26(request):
    try:
        edition_2026 = FlamesEdition.objects.get(year=2026)
        courses = FlamesCourse.objects.filter(edition=edition_2026, is_active=True).order_by('title')
    except FlamesEdition.DoesNotExist:
        edition_2026 = None
        courses = FlamesCourse.objects.none()
    return render(request, "home/flames26/flames26.html", {
        'courses': courses,
        'edition': edition_2026,
    })


# ============================ FLAMES 26 TRACK DETAIL PAGE ==========================

FLAMES26_TRACKS = {
    "full-stack-gen-ai": {
        "title": "Full Stack with Gen AI",
        "tagline": '"Build real products, not clones."',
        "icon": "fas fa-layer-group",
        "level": "Beginner",
        "badge_class": "badge-beginner",
        "register_url": "#",
        "projects": [
            {
                "icon": "fas fa-globe",
                "title": "AI-Powered Portfolio Website",
                "desc": "A personal portfolio with an AI chatbot that answers visitor questions about you."
            },
            {
                "icon": "fas fa-tasks",
                "title": "Smart Task Manager",
                "desc": "Full-stack task app with AI-assisted prioritisation and deadline suggestions."
            },
            {
                "icon": "fas fa-comments",
                "title": "Real-Time Chat App with AI Bot",
                "desc": "A Django Channels chat app with an embedded AI assistant bot."
            },
        ],
        "roadmap": [
            {
                "week": 1, "days": "1–7",
                "title": "HTML, CSS & Responsive Design",
                "topics": ["Semantic HTML5 structure", "Flexbox & Grid layouts", "Responsive design principles", "Build 2 static web pages"]
            },
            {
                "week": 2, "days": "8–14",
                "title": "JavaScript Fundamentals",
                "topics": ["DOM manipulation & events", "Fetch API & async/await", "ES6+ modern syntax", "Build an interactive UI component"]
            },
            {
                "week": 3, "days": "15–21",
                "title": "Django Backend Foundations",
                "topics": ["Project setup, URLs & Views", "Templates & static files", "Models & Django ORM", "Convert static site to Django"]
            },
            {
                "week": 4, "days": "22–28",
                "title": "CRUD & Authentication",
                "topics": ["Forms & ModelForms", "User signup, login, logout", "Login-required views", "Build a full CRUD system"]
            },
            {
                "week": 5, "days": "29–35",
                "title": "REST APIs & Gen AI Integration",
                "topics": ["Django REST Framework basics", "OpenAI / Gemini API calls", "Prompt engineering fundamentals", "Add AI feature to your project"]
            },
            {
                "week": 6, "days": "36–45",
                "title": "Deployment & Capstone Project",
                "topics": ["Deploy on Render / Railway", "Environment variables & security", "Capstone: Full-stack AI web app", "Demo day & portfolio polish"]
            },
        ],
        "tech_stack": ["HTML5", "CSS3", "JavaScript", "Django", "Django REST Framework", "SQLite / PostgreSQL", "OpenAI API", "Gemini API", "Git & GitHub", "Render / Railway"],
        "gains": [
            {"icon": "fas fa-laptop-code", "label": "Portfolio", "value": "Live deployed web app"},
            {"icon": "fas fa-robot", "label": "Skill", "value": "AI integration in apps"},
            {"icon": "fas fa-code-branch", "label": "GitHub", "value": "Public commit history"},
            {"icon": "fas fa-certificate", "label": "Certificate", "value": "Completion certificate"},
        ],
        "testimonials": [
            {"quote": "I deployed my first Django app with an AI chatbot in week 5. I didn't think that was possible 45 days ago.", "author": "FLAMES '25 · Full Stack Track"},
            {"quote": "The structure of daily tasks made it impossible to procrastinate. I shipped more in 6 weeks than in 6 months before.", "author": "FLAMES '25 · Full Stack Track"},
            {"quote": "Building something real — not a tutorial clone — changed how I think about coding entirely.", "author": "FLAMES '25 · Full Stack Track"},
        ]
    },

    "dsa-java-cpp": {
        "title": "DSA with Java / C++",
        "tagline": '"Stop fearing coding rounds."',
        "icon": "fab fa-java",
        "level": "Intermediate",
        "badge_class": "badge-intermediate",
        "register_url": "#",
        "projects": [
            {
                "icon": "fas fa-sitemap",
                "title": "Custom Data Structure Library",
                "desc": "Build your own Stack, Queue, LL, and BST implementations from scratch."
            },
            {
                "icon": "fas fa-search",
                "title": "Algorithmic Problem Set Portfolio",
                "desc": "150+ solved LeetCode-style problems documented with patterns and complexity analysis."
            },
            {
                "icon": "fas fa-users",
                "title": "Mock Interview Simulator",
                "desc": "A command-line app that presents random DSA problems and tracks your timing."
            },
        ],
        "roadmap": [
            {
                "week": 1, "days": "1–7",
                "title": "Logic Building & Arrays",
                "topics": ["Java / C++ syntax review", "Time & space complexity", "Arrays: traversal, two-pointer", "Pattern printing & logic problems"]
            },
            {
                "week": 2, "days": "8–14",
                "title": "Strings, Hashing & Sliding Window",
                "topics": ["String manipulation techniques", "HashMap & HashSet patterns", "Fixed & variable sliding window", "Kadane's algorithm & subarrays"]
            },
            {
                "week": 3, "days": "15–21",
                "title": "Binary Search & Recursion",
                "topics": ["Binary search on answer space", "Recursion tree & call stack", "Backtracking fundamentals", "Subsequences & permutations"]
            },
            {
                "week": 4, "days": "22–28",
                "title": "Linked Lists & Stacks/Queues",
                "topics": ["Singly & doubly linked lists", "Fast & slow pointer technique", "Monotonic stack patterns", "Queue & deque applications"]
            },
            {
                "week": 5, "days": "29–35",
                "title": "Trees & Heaps",
                "topics": ["Binary tree DFS & BFS traversals", "BST operations & validation", "Heap & priority queue", "Top-K element problems"]
            },
            {
                "week": 6, "days": "36–45",
                "title": "Graphs & Interview Prep",
                "topics": ["BFS/DFS on graphs", "Topological sort & cycle detection", "Mock interview sessions", "Resume & LinkedIn polish"]
            },
        ],
        "tech_stack": ["Java", "C++", "IntelliJ IDEA / VS Code", "LeetCode", "Git & GitHub", "OOP Concepts", "Collections Framework"],
        "gains": [
            {"icon": "fas fa-trophy", "label": "Skill", "value": "Crack coding rounds"},
            {"icon": "fas fa-file-code", "label": "Portfolio", "value": "150+ solved problems"},
            {"icon": "fas fa-user-tie", "label": "Prep", "value": "Mock interview ready"},
            {"icon": "fas fa-certificate", "label": "Certificate", "value": "Completion certificate"},
        ],
        "testimonials": [
            {"quote": "I went from not being able to solve a simple array problem to clearing the DSA round at my first placement attempt.", "author": "FLAMES '25 · DSA Track"},
            {"quote": "The pattern-based approach is a game changer. Once I saw the patterns, everything clicked.", "author": "FLAMES '25 · DSA Track"},
            {"quote": "Daily problems, daily accountability. That's what made the difference. Not another YouTube playlist.", "author": "FLAMES '25 · DSA Track"},
        ]
    },

    "data-analytics-ai": {
        "title": "Data Analytics with AI Tools",
        "tagline": '"Learn what companies actually use."',
        "icon": "fas fa-chart-bar",
        "level": "Beginner",
        "badge_class": "badge-beginner",
        "register_url": "#",
        "projects": [
            {
                "icon": "fas fa-chart-line",
                "title": "Sales Performance Dashboard",
                "desc": "End-to-end analytics pipeline from raw CSV to an interactive Power BI dashboard."
            },
            {
                "icon": "fas fa-brain",
                "title": "AI-Assisted EDA Report",
                "desc": "Automated exploratory data analysis using AI tools to generate insights."
            },
            {
                "icon": "fas fa-database",
                "title": "SQL Analytics on Real Dataset",
                "desc": "Complex SQL queries and aggregations on a 100k+ row real-world dataset."
            },
        ],
        "roadmap": [
            {
                "week": 1, "days": "1–7",
                "title": "Python for Data Analysis",
                "topics": ["Python fundamentals recap", "NumPy arrays & operations", "Pandas DataFrames & Series", "Reading & writing CSV/Excel"]
            },
            {
                "week": 2, "days": "8–14",
                "title": "Data Cleaning & EDA",
                "topics": ["Handling nulls, duplicates, outliers", "Matplotlib & Seaborn visualisations", "AI-assisted EDA tools", "Draw insights from real dataset"]
            },
            {
                "week": 3, "days": "15–21",
                "title": "SQL for Analytics",
                "topics": ["SELECT, WHERE, GROUP BY, JOINS", "Window functions", "Subqueries & CTEs", "Analytics queries on real DB"]
            },
            {
                "week": 4, "days": "22–28",
                "title": "Business Intelligence Tools",
                "topics": ["Power BI / Tableau basics", "Building interactive dashboards", "KPIs & data storytelling", "Connect BI tool to SQL DB"]
            },
            {
                "week": 5, "days": "29–35",
                "title": "AI in Analytics",
                "topics": ["ChatGPT & Gemini for data tasks", "AI-generated SQL queries", "Automated report generation", "AI-assisted data interpretation"]
            },
            {
                "week": 6, "days": "36–45",
                "title": "Capstone Project & Presentation",
                "topics": ["Choose a real-world dataset", "Full EDA → dashboard pipeline", "Present findings to the cohort", "Portfolio & LinkedIn update"]
            },
        ],
        "tech_stack": ["Python", "Pandas", "NumPy", "Matplotlib", "Seaborn", "SQL", "Power BI", "Tableau", "ChatGPT / Gemini", "Excel", "Jupyter Notebook"],
        "gains": [
            {"icon": "fas fa-chart-pie", "label": "Skill", "value": "End-to-end analytics"},
            {"icon": "fas fa-table", "label": "Tool", "value": "Power BI / Tableau"},
            {"icon": "fas fa-robot", "label": "Bonus", "value": "AI for data tasks"},
            {"icon": "fas fa-certificate", "label": "Certificate", "value": "Completion certificate"},
        ],
        "testimonials": [
            {"quote": "I built a full dashboard from raw data and presented it like a data analyst. That's what got me my internship.", "author": "FLAMES '25 · Analytics Track"},
            {"quote": "Using AI tools for EDA cut my analysis time in half. That's a real-world skill companies want right now.", "author": "FLAMES '25 · Analytics Track"},
            {"quote": "The SQL week alone was worth it. I could finally understand business data and ask the right questions.", "author": "FLAMES '25 · Analytics Track"},
        ]
    },

    "gen-ai-agentic": {
        "title": "Gen AI & Agentic AI",
        "tagline": '"Build systems, not prompts."',
        "icon": "fas fa-robot",
        "level": "Intermediate",
        "badge_class": "badge-intermediate",
        "register_url": "#",
        "projects": [
            {
                "icon": "fas fa-brain",
                "title": "RAG-Based Knowledge Bot",
                "desc": "Upload any PDF and chat with it using Retrieval-Augmented Generation."
            },
            {
                "icon": "fas fa-cogs",
                "title": "Multi-Step AI Agent",
                "desc": "An agent that searches the web, reads pages, and summarises findings autonomously."
            },
            {
                "icon": "fas fa-code",
                "title": "AI Code Review Pipeline",
                "desc": "Automated pipeline that reads GitHub PRs and suggests improvements using an LLM."
            },
        ],
        "roadmap": [
            {
                "week": 1, "days": "1–7",
                "title": "LLM Fundamentals & APIs",
                "topics": ["How LLMs work (transformers, tokens)", "OpenAI & Gemini API integration", "Prompt engineering patterns", "Build your first AI-powered script"]
            },
            {
                "week": 2, "days": "8–14",
                "title": "RAG — Retrieval-Augmented Generation",
                "topics": ["What is RAG and why it matters", "Text embeddings & vector databases", "Pinecone / Chroma setup", "Build a document Q&A bot"]
            },
            {
                "week": 3, "days": "15–21",
                "title": "LangChain & Chains",
                "topics": ["LangChain core concepts & chains", "Memory & conversation history", "Document loaders & splitters", "Build a multi-turn chatbot"]
            },
            {
                "week": 4, "days": "22–28",
                "title": "AI Agents & Tool Use",
                "topics": ["What is an AI Agent?", "LangChain Agents & Tools", "ReAct pattern", "Build an agent that uses real tools"]
            },
            {
                "week": 5, "days": "29–35",
                "title": "LangGraph & Agentic Pipelines",
                "topics": ["LangGraph graph-based workflows", "Multi-agent orchestration", "Human-in-the-loop patterns", "Build a multi-step agentic pipeline"]
            },
            {
                "week": 6, "days": "36–45",
                "title": "Deployment & Capstone",
                "topics": ["Serve agents via FastAPI", "Deploy on cloud (Render / GCP)", "Capstone: full agentic system", "Demo day & portfolio packaging"]
            },
        ],
        "tech_stack": ["Python", "OpenAI API", "Gemini API", "LangChain", "LangGraph", "Pinecone", "ChromaDB", "FastAPI", "Docker", "Git & GitHub"],
        "gains": [
            {"icon": "fas fa-robot", "label": "Skill", "value": "Build AI agents"},
            {"icon": "fas fa-database", "label": "Tool", "value": "VectorDB & RAG systems"},
            {"icon": "fas fa-project-diagram", "label": "Project", "value": "Deployed agentic app"},
            {"icon": "fas fa-certificate", "label": "Certificate", "value": "Completion certificate"},
        ],
        "testimonials": [
            {"quote": "I built a RAG system for my college's question papers. Now students at my college use it daily. That's real impact.", "author": "FLAMES '25 · Gen AI Track"},
            {"quote": "LangGraph was mind-bending. Once I understood it, I could build systems I thought only big companies could build.", "author": "FLAMES '25 · Gen AI Track"},
            {"quote": "Most people know how to write prompts. After this, I know how to build systems. That's a different league.", "author": "FLAMES '25 · Gen AI Track"},
        ]
    },

    "mobile-app-gen-ai": {
        "title": "Mobile App Dev with Gen AI",
        "tagline": '"Ship apps, not ideas."',
        "icon": "fas fa-mobile-alt",
        "level": "Beginner",
        "badge_class": "badge-beginner",
        "register_url": "#",
        "projects": [
            {
                "icon": "fas fa-camera",
                "title": "AI Photo Analyser App",
                "desc": "A mobile app that analyses photos using Gemini Vision and describes what it sees."
            },
            {
                "icon": "fas fa-shopping-cart",
                "title": "E-Commerce Mobile App",
                "desc": "Full-featured shopping app with Firebase backend and AI product recommendations."
            },
            {
                "icon": "fas fa-microphone-alt",
                "title": "AI Voice Notes App",
                "desc": "Record audio, transcribe with AI, and get a structured summary — all in a mobile app."
            },
        ],
        "roadmap": [
            {
                "week": 1, "days": "1–7",
                "title": "Flutter / React Native Fundamentals",
                "topics": ["Dart basics (Flutter) or JS refresh (RN)", "Widgets / Components architecture", "UI layout: Rows, Columns, Stacks", "Build your first mobile screen"]
            },
            {
                "week": 2, "days": "8–14",
                "title": "Navigation & State Management",
                "topics": ["Multi-screen navigation", "State management basics (Provider / useState)", "Form handling & validation", "Build a multi-screen mini app"]
            },
            {
                "week": 3, "days": "15–21",
                "title": "Firebase Backend",
                "topics": ["Firebase Auth (email & Google)", "Firestore database CRUD", "Firebase Storage for media", "Authenticated app with real DB"]
            },
            {
                "week": 4, "days": "22–28",
                "title": "AI Feature Integration",
                "topics": ["Gemini API in mobile apps", "Image & text analysis", "AI-powered chat in the app", "Add AI feature to your Firebase app"]
            },
            {
                "week": 5, "days": "29–35",
                "title": "Device APIs & Performance",
                "topics": ["Camera, GPS, notifications", "App performance optimisation", "Offline support & caching", "Polish app for production"]
            },
            {
                "week": 6, "days": "36–45",
                "title": "Deployment & Capstone",
                "topics": ["Build APK / IPA for distribution", "Publish to Play Store (test track)", "Capstone: full AI mobile app", "Demo day & portfolio update"]
            },
        ],
        "tech_stack": ["Flutter / React Native", "Dart / JavaScript", "Firebase", "Firestore", "Gemini API", "REST APIs", "Git & GitHub", "Android Studio / Xcode"],
        "gains": [
            {"icon": "fas fa-mobile-alt", "label": "Deliverable", "value": "Live published app"},
            {"icon": "fas fa-robot", "label": "Skill", "value": "AI features in mobile"},
            {"icon": "fas fa-fire", "label": "Backend", "value": "Firebase mastery"},
            {"icon": "fas fa-certificate", "label": "Certificate", "value": "Completion certificate"},
        ],
        "testimonials": [
            {"quote": "I published my first app to the Play Store in week 6. That moment felt unreal. Nothing beats it.", "author": "FLAMES '25 · Mobile Track"},
            {"quote": "I thought mobile dev was hard. The daily structure made it manageable. One concept at a time, every day.", "author": "FLAMES '25 · Mobile Track"},
            {"quote": "My app is now being used by my college friends. Building something people actually use is a different feeling.", "author": "FLAMES '25 · Mobile Track"},
        ]
    },
}


def flames26_track_detail(request, track_slug):
    track = FLAMES26_TRACKS.get(track_slug)
    if not track:
        from django.http import Http404
        raise Http404("Track not found")
    # Also fetch the DB course so the template CTA can link to registration
    course = FlamesCourse.objects.filter(slug=track_slug, is_active=True).first()
    return render(request, "home/flames26/track_detail.html", {
        "track":  track,
        "course": course,
    })


# ============================ FLAMES 26 REGISTRATION PAGE ==========================

def flames26_register(request, track_slug):
    """
    Registration page for a specific FLAMES '26 track.
    Fully DB-driven: the course MUST exist in the DB (linked to the 2026 edition)
    or the view returns 404.
    Submission is handled by the existing register_flames view.
    """
    from django.http import Http404

    # Require the 2026 edition to exist
    try:
        edition_2026 = FlamesEdition.objects.get(year=2026)
    except FlamesEdition.DoesNotExist:
        raise Http404("FLAMES 2026 edition has not been set up yet.")

    # Hard 404 if the slug doesn't match an active DB course in that edition
    course = get_object_or_404(
        FlamesCourse,
        slug=track_slug,
        edition=edition_2026,
        is_active=True,
    )

    active_edition = _get_active_edition()

    # Duplicate-registration guard for logged-in users
    if request.user.is_authenticated and active_edition:
        already = FlamesRegistration.objects.filter(
            user=request.user,
            course=course,
            edition=active_edition,
        ).exclude(status='Rejected').exists()
        if already:
            messages.warning(
                request,
                f"You are already registered for {course.title}."
            )
            return redirect('student_flames')

    colleges = [
        "GLA University, Mathura",
        "Lovely Professional University, Jalandhar",
        "Shiv Nadar University, Greater Noida",
        "Delhi Technological University, Delhi",
        "Acharya Narendra Dev College, Delhi",
        "LDRP Institute of Technology and Research, Gandhinagar",
        "BSA College of Engineering, Mathura",
        "Other",
    ]

    return render(request, "home/flames26/flames26_register.html", {
        "course":   course,
        "edition":  active_edition if request.user.is_authenticated else _get_active_edition(),
        "colleges": colleges,
    })

