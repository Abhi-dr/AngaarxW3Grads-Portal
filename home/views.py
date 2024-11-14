from django.shortcuts import render, redirect
from django.contrib import messages as message
from .models import Flames

def home(request):
    return render(request, "home/index.html")

def about(request):
    return render(request, "home/about.html")

def angaar_plus(request):
    return render(request, "home/angaar_plus.html")

def flames(request):
    
    if request.method == "POST":
        name = request.POST.get("name")
        whatsapp_number = request.POST.get("whatsapp_number")
        contact_number = request.POST.get("contact_number")
        college = request.POST.get("college")
        mode = request.POST.get("mode")
        
        flames = Flames(name=name, whatsapp_number=whatsapp_number, contact_number=contact_number, college=college, mode=mode)
        flames.save()
        
        message.success(request, "Your details have been submitted successfully.")
        
        return redirect("flames")
    
    return render(request, "home/flames.html")


# ========================= SCHOLARSHIP TEST =========================

def scholarship_test(request):
    return render(request, "home/scholarship_test.html")