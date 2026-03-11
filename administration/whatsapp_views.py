from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from home.models import FreeClassWhatsappGroupLink
from angaar_hai.custom_decorators import admin_required


@login_required(login_url='login')
@staff_member_required
@admin_required
def whatsapp_groups(request):
    groups = FreeClassWhatsappGroupLink.objects.all()
    # Available choices that haven't been used yet
    used_codes = list(groups.values_list('course_code', flat=True))
    available_choices = [
        (code, label)
        for code, label in FreeClassWhatsappGroupLink.COURSE_CHOICES
        if code not in used_codes
    ]
    return render(request, 'administration/whatsapp/whatsapp_groups.html', {
        'groups': groups,
        'available_choices': available_choices,
    })


@login_required(login_url='login')
@staff_member_required
@admin_required
def add_whatsapp_group(request):
    if request.method == 'POST':
        course_code = request.POST.get('course_code', '').strip()
        whatsapp_link = request.POST.get('whatsapp_link', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        valid_codes = [code for code, _ in FreeClassWhatsappGroupLink.COURSE_CHOICES]
        if course_code not in valid_codes:
            messages.error(request, 'Invalid course selected.')
            return redirect('admin_whatsapp_groups')

        if FreeClassWhatsappGroupLink.objects.filter(course_code=course_code).exists():
            messages.error(request, f'A WhatsApp link for "{course_code}" already exists.')
            return redirect('admin_whatsapp_groups')

        FreeClassWhatsappGroupLink.objects.create(
            course_code=course_code,
            whatsapp_link=whatsapp_link,
            is_active=is_active,
        )
        messages.success(request, 'WhatsApp group link added successfully.')
        return redirect('admin_whatsapp_groups')

    return redirect('admin_whatsapp_groups')


@login_required(login_url='login')
@staff_member_required
@admin_required
def edit_whatsapp_group(request, pk):
    group = get_object_or_404(FreeClassWhatsappGroupLink, pk=pk)

    if request.method == 'POST':
        whatsapp_link = request.POST.get('whatsapp_link', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        group.whatsapp_link = whatsapp_link
        group.is_active = is_active
        group.save()

        messages.success(request, 'WhatsApp group link updated successfully.')
        return redirect('admin_whatsapp_groups')

    return redirect('admin_whatsapp_groups')


@login_required(login_url='login')
@staff_member_required
@admin_required
def delete_whatsapp_group(request, pk):
    group = get_object_or_404(FreeClassWhatsappGroupLink, pk=pk)
    group.delete()
    messages.success(request, 'WhatsApp group link deleted successfully.')
    return redirect('admin_whatsapp_groups')


@login_required(login_url='login')
@staff_member_required
@admin_required
def toggle_whatsapp_group(request, pk):
    group = get_object_or_404(FreeClassWhatsappGroupLink, pk=pk)
    group.is_active = not group.is_active
    group.save()
    return JsonResponse({'success': True, 'is_active': group.is_active})
