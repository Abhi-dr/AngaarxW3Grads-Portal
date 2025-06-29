from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from home.models import FlamesRegistration
from .payment_utils import PaymentGateway

from angaar_hai.mail_utility import send_flames_confirmation_mail

@login_required
def initiate_payment(request, registration_id):
    """
    Initiate payment process for a specific registration
    """
    # Get the registration object
    registration = get_object_or_404(FlamesRegistration, id=registration_id, user=request.user)
    
    # Check if already paid
    if registration.payment_id:
        return JsonResponse({
            'success': False,
            'error': 'Payment already made for this registration'
        })
    
    # Generate payment order
    order_data = PaymentGateway.generate_order(registration_id, request)
    
    if not order_data.get('success', False):
        return JsonResponse(order_data)
    
    # Return order details to the frontend
    return JsonResponse(order_data)

@csrf_exempt
def payment_callback(request):
    """
    Handle payment callback from Razorpay
    """
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        registration_id = request.POST.get('registration_id', '')
        
        # Verify payment
        if payment_id and order_id and signature:
            is_verified = PaymentGateway.verify_payment(payment_id, order_id, signature, registration_id)
            
            if is_verified:
                # Redirect to success page                
                return redirect(reverse('payment_success', kwargs={'registration_id': registration_id}))
    
    # If verification fails or method is not POST, redirect to failure page
    return redirect(reverse('payment_failure'))

@login_required
def payment_success(request, registration_id):
    """
    Payment success page
    """
    registration = get_object_or_404(FlamesRegistration, id=registration_id)
    
    context = {
        'registration': registration,
        'course': registration.course,
        'payment_id': registration.payment_id
    }
    
    #  Sending mail
                
    # send_flames_confirmation_mail(
    #     request.user.email,
    #     request.user.first_name,
    #     registration.course.title
    # )
    
    return render(request, 'student/flames/payment_success.html', context)

@login_required
def payment_failure(request):
    """
    Payment failure page
    """
    return render(request, 'student/flames/payment_failure.html')

@login_required
def payment_status(request, registration_id):
    """
    Check payment status for a specific registration
    """
    registration = get_object_or_404(FlamesRegistration, id=registration_id, user=request.user)
    
    if not registration.payment_id:
        return JsonResponse({
            'status': 'not_initiated',
            'registration_id': registration_id
        })
    
    # Get payment status from gateway
    status_data = PaymentGateway.get_payment_status(registration.payment_id)
    
    return JsonResponse(status_data)
