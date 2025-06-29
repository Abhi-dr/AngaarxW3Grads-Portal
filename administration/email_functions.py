"""
Email functions for the FLAMES admin panel
These functions will be added to flames_views.py
"""

@login_required
def admin_flames_emails(request):
    """
    View for sending bulk emails to FLAMES registrants
    """
    courses = FlamesCourse.objects.all()
    registrations = FlamesRegistration.objects.all().select_related('course', 'student')
    
    # Get registration statistics
    total_recipients = registrations.count()
    completed_registrations = registrations.filter(status='COMPLETED').count()
    pending_registrations = registrations.filter(status='PENDING').count()
    solo_registrations = registrations.filter(registration_mode='SOLO').count()
    team_registrations = registrations.filter(registration_mode='TEAM').count()
    
    if request.method == 'POST':
        # Get email data from form
        course_filter = request.POST.get('course_filter')
        status_filter = request.POST.get('status_filter')
        registration_mode = request.POST.get('registration_mode')
        email_subject = request.POST.get('email_subject')
        email_content = request.POST.get('email_content')
        send_test = request.POST.get('send_test') == 'on'
        
        # Filter recipients based on selection
        recipients = FlamesRegistration.objects.all().select_related('course', 'student')
        
        if course_filter and course_filter != 'all':
            recipients = recipients.filter(course_id=course_filter)
            
        if status_filter and status_filter != 'all':
            recipients = recipients.filter(status=status_filter)
            
        if registration_mode and registration_mode != 'all':
            recipients = recipients.filter(registration_mode=registration_mode)
        
        # Send test email to admin if requested
        if send_test:
            admin_email = request.user.email
            admin_name = f"{request.user.first_name} {request.user.last_name}"
            course_name = "Test Course"
            
            # Send a test email
            html_content = email_content.replace('{{name}}', admin_name)
            html_content = html_content.replace('{{course_info}}', f'<p style="font-size: 16px; color: #ff6b35;"><strong>Course: {course_name}</strong></p>')
            
            send_flames_email(admin_email, admin_name, email_subject, html_content)
            
            messages.success(request, f"Test email sent to {admin_email}")
            return redirect('admin_flames_emails')
        
        # Send real emails to all recipients
        sent_count = 0
        error_count = 0
        
        for registration in recipients:
            if registration.student and registration.student.email:
                student_email = registration.student.email
                student_name = f"{registration.student.first_name} {registration.student.last_name}"
                course_name = registration.course.title
                
                # Prepare course information including pricing details
                price_info = ""
                if registration.registration_mode == 'TEAM':
                    # Special team pricing calculation: (course price * 5) - (499 * 5)
                    price_info = f"Team Registration: ₹{registration.payable_amount} (5 members)"  
                else:
                    price_info = f"Solo Registration: ₹{registration.payable_amount}"
                
                # Replace placeholders
                html_content = email_content.replace('{{name}}', student_name)
                course_info_html = f'<p style="font-size: 16px; color: #ff6b35;"><strong>Course: {course_name}</strong></p>'
                course_info_html += f'<p style="font-size: 14px; color: #ff6b35;">{price_info}</p>'
                html_content = html_content.replace('{{course_info}}', course_info_html)
                
                try:
                    send_flames_email(student_email, student_name, email_subject, html_content)
                    sent_count += 1
                except Exception as e:
                    print(f"Error sending email to {student_email}: {str(e)}")
                    error_count += 1
        
        messages.success(request, f"Successfully sent {sent_count} emails with {error_count} errors.")
        return redirect('admin_flames_emails')
    
    context = {
        'courses': courses,
        'total_recipients': total_recipients,
        'completed_registrations': completed_registrations,
        'pending_registrations': pending_registrations,
        'solo_registrations': solo_registrations,
        'team_registrations': team_registrations,
    }
    
    return render(request, 'administration/flames/send_emails.html', context)


@login_required
def admin_count_flames_email_recipients(request):
    """
    Count recipients based on filter criteria
    """
    course_filter = request.GET.get('course_filter')
    status_filter = request.GET.get('status_filter')
    registration_mode = request.GET.get('registration_mode')
    
    # Start with all registrations
    recipients = FlamesRegistration.objects.all().select_related('student')
    
    # Apply filters
    if course_filter and course_filter != 'all':
        recipients = recipients.filter(course_id=course_filter)
        
    if status_filter and status_filter != 'all':
        recipients = recipients.filter(status=status_filter)
        
    if registration_mode and registration_mode != 'all':
        recipients = recipients.filter(registration_mode=registration_mode)
    
    # Count valid recipients (those with an email)
    valid_recipients = 0
    for registration in recipients:
        if registration.student and registration.student.email:
            valid_recipients += 1
    
    return JsonResponse({
        'success': True,
        'count': valid_recipients
    })


def send_flames_email(to, name, subject, html_content):
    """
    Helper function to send a formatted FLAMES email
    """
    from_email = 'noreply@theangaarbatch.in'
    to_email = [to]
    
    from_name = "The Angaar Batch"
    from_email_full = f"{from_name} <{from_email}>"

    email = EmailMultiAlternatives(subject, '', from_email_full, to_email)
    email.attach_alternative(html_content, 'text/html')
    email.send()
    
    print(f"FLAMES EMAIL SENT! to {to_email}")
