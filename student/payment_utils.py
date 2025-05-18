import json
import requests
import logging
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from home.models import FlamesRegistration

logger = logging.getLogger(__name__)

# utils/razorpay_client.py

import razorpay
from django.conf import settings

# Initialize Razorpay client with live mode
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Force live mode (this is the key change to switch from test to live mode)
razorpay_client.set_app_details({"title": "Angaar FLAMES", "version": "1.0"})


class PaymentGateway:
    """
    Payment Gateway wrapper for Razorpay integration.
    This class handles all payment-related functionality separate from the main views.
    """
    
    @staticmethod
    def generate_order(registration_id, request=None):
        """
        Generate a payment order for a registration.
        
        Args:
            registration_id: The ID of the FlamesRegistration
            request: The HTTP request (for generating callback URLs)
            
        Returns:
            dict: Order details if successful, error information otherwise
        """
        try:
            # Get registration object
            registration = FlamesRegistration.objects.get(id=registration_id)
            
            # Check if registration is rejected
            if registration.status == 'Rejected':
                return {
                    'success': False,
                    'error': 'Registration has been rejected. Payment not allowed.'
                }
                
            # Check if already paid or completed
            if registration.status == 'Completed' or registration.payment_id:
                return {
                    'success': False,
                    'error': 'Payment has already been completed for this registration.'
                }
            
            # Ensure we have a valid payable amount
            if not registration.payable_amount or registration.payable_amount <= 0:
                return {
                    'success': False,
                    'error': 'Invalid payment amount'
                }
            
            # Format amount for Razorpay (in paise - multiply by 100)
            amount = int(float(registration.payable_amount) * 100)
            
            # Create receipt ID
            receipt = f"receipt_{registration_id}_{int(amount)}"
            
            # Create actual Razorpay order
            try:
                # Create order in Razorpay
                order_params = {
                    'amount': amount,
                    'currency': 'INR',
                    'receipt': receipt,
                    'notes': {
                        'registration_id': registration_id,
                        'course': registration.course.title,
                        'registration_mode': registration.registration_mode
                    }
                }
                
                # Create the order using Razorpay client
                razorpay_order = razorpay_client.order.create(order_params)
                
                # Prepare response data
                order_data = {
                    'success': True,
                    'order_id': razorpay_order['id'],  # Actual Razorpay order ID
                    'amount': amount,
                    'currency': 'INR',
                    'registration_id': registration_id,
                    # Include callback URLs if request is provided
                    'callback_url': request.build_absolute_uri(reverse('payment_callback')) if request else None,
                    # Add additional data needed for the frontend
                    'name': registration.course.title,
                    'description': f"Registration for {registration.course.title}",
                    'prefill': {
                        'name': f"{registration.user.first_name} {registration.user.last_name}",
                        'email': registration.user.email,
                        'contact': registration.user.mobile_number
                    },
                }
            except Exception as e:
                print(f"Razorpay order creation failed: {str(e)}")
                return {
                    'success': False,
                    'error': f"Failed to create payment order: {str(e)}"
                }
            
            # Log the order creation
            print(f"Payment order generated for registration {registration_id}")
            
            return order_data
            
        except FlamesRegistration.DoesNotExist:
            print(f"Registration {registration_id} not found")
            return {
                'success': False,
                'error': 'Registration not found'
            }
        except Exception as e:
            print(f"Error generating payment order: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def verify_payment(payment_id, order_id, signature, registration_id):
        """
        Verify a payment using the Razorpay signature.
        
        Args:
            payment_id: Razorpay payment ID
            order_id: Razorpay order ID
            signature: Razorpay signature
            registration_id: FlamesRegistration ID
            
        Returns:
            bool: True if payment is verified, False otherwise
        """
        try:
            # Get the registration
            registration = FlamesRegistration.objects.get(id=registration_id)
            
            # Check if registration is rejected
            if registration.status == 'Rejected':
                print(f"Payment attempted for rejected registration {registration_id}")
                return False
                
            # Verify the payment signature
            params_dict = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            }
            
            try:
                # Verify signature
                razorpay_client.utility.verify_payment_signature(params_dict)
                
                # If we reach here, signature is valid
                # Update payment details and set status to Completed
                registration.payment_id = payment_id
                registration.status = 'Completed'  # Set to Completed after successful payment
                registration.save()
                
                print(f"Payment {payment_id} verified for registration {registration_id}")
                return True
            except Exception as e:
                print(f"Payment signature verification failed: {str(e)}")
                return False
            
        except Exception as e:
            print(f"Error verifying payment: {str(e)}")
            return False
    
    @staticmethod
    def get_payment_status(payment_id):
        """
        Get the status of a payment from Razorpay.
        
        Args:
            payment_id: Razorpay payment ID
            
        Returns:
            dict: Payment status information
        """
        # This is a placeholder. In production, you would call the Razorpay API here
        return {
            'status': 'pending',  # Or 'authorized', 'captured', 'failed', etc.
            'payment_id': payment_id
        }
