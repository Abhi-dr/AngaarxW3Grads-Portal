from django.urls import path
from . import payment_views

urlpatterns = [
    # Payment-related URLs
    path('initiate-payment/<int:registration_id>/', payment_views.initiate_payment, name='initiate_payment'),
    path('payment-callback/', payment_views.payment_callback, name='payment_callback'),
    path('payment-success/<int:registration_id>/', payment_views.payment_success, name='payment_success'),
    path('payment-failure/', payment_views.payment_failure, name='payment_failure'),
    path('payment-status/<int:registration_id>/', payment_views.payment_status, name='payment_status'),
]
