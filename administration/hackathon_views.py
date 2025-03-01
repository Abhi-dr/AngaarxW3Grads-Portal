from django.shortcuts import render, redirect 
from django.contrib.admin.views.decorators import staff_member_required
from angaar_hai.custom_decorators import admin_required
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from student.models import Hackathon
from django.contrib import messages
from django.shortcuts import get_object_or_404


# ================================== HACKATHON ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def hackathon_list(request):
    return render(request, "administration/hackathon/all_hackathons.html")


# ================================== FETCH HACKATHONS =============================

@login_required(login_url='login')
def fetch_hackathons(request):

    hackathons = Hackathon.objects.all().order_by("start_date")
    
    hackathon_data = [
        {
            "id": hackathon.id,
            "name": hackathon.name,
            "start_date": hackathon.start_date.strftime("%Y-%m-%d"),
            "end_date": hackathon.end_date.strftime("%Y-%m-%d"),
            "location": hackathon.location,
            "registration_deadline": hackathon.registration_deadline.strftime("%Y-%m-%d"),
            "prize_pool": hackathon.prize_pool,
            "thumbnail": hackathon.thumbnail.url if hackathon.thumbnail else "/static/default-thumbnail.jpg",
            "website": hackathon.website,
            "is_active": hackathon.get_active_status(),
        }
        for hackathon in hackathons
    ]
    
    return JsonResponse(
        {
            'success': True,
            "hackathons": hackathon_data
        }, 
        status=200
    )



# ================================== ADD HACKATHON ===================================


@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def add_hackathon(request):

    if request.method == "POST":

        name = request.POST.get("name")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        location = request.POST.get("location")
        registration_deadline = request.POST.get("registration_deadline")
        prize_pool = request.POST.get("prize_pool")
        thumbnail = request.FILES.get("thumbnail")
        website = request.POST.get("website")

        Hackathon.objects.create(
            name=name,
            start_date=start_date,
            end_date=end_date,
            location=location,
            registration_deadline=registration_deadline,
            prize_pool=prize_pool,
            thumbnail=thumbnail,
            website=website,
        )

        messages.success(request, "Hackathon added successfully")

        return redirect("administrator_hackathon_list")  

    return render(request, "administration/hackathon/add_hackathon.html")




# ================================= EDIT HACKATHON ===================================


@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def edit_hackathon(request, hackathon_id):

    hackathon = get_object_or_404(Hackathon, id=hackathon_id)

    if request.method == "POST":
        hackathon.name = request.POST.get("name")
        hackathon.start_date = request.POST.get("start_date")
        hackathon.end_date = request.POST.get("end_date")
        hackathon.location = request.POST.get("location")
        hackathon.registration_deadline = request.POST.get("registration_deadline")
        hackathon.prize_pool = request.POST.get("prize_pool")
        hackathon.website = request.POST.get("website")

        if "thumbnail" in request.FILES:
            hackathon.thumbnail = request.FILES["thumbnail"]

        hackathon.save()  

        messages.success(request, "Hackathon updated successfully")

        return redirect("administrator_hackathon_list")  

    return render(request, "administration/hackathon/edit_hackathon.html", {"hackathon": hackathon})


# =============================== DELETE HACKATHON ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def delete_hackathon(request, hackathon_id):

    hackathon = get_object_or_404(Hackathon, id=hackathon_id)

    hackathon.delete()

    messages.success(request, "Hackathon deleted successfully")

    return redirect("administrator_hackathon_list")

