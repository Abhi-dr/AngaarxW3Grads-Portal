from django.urls import re_path
from administration.consumers import EnrollmentRequestConsumer

print("\n\n\nExecuted\n\n\n")

websocket_urlpatterns = [
    re_path(r'ws/enrollment_requests/$', EnrollmentRequestConsumer.as_asgi()),
]
