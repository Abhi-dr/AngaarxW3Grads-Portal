import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import administration  # Ensure this is correct

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'angaar_hai.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            administration.routing.websocket_urlpatterns
        )
    ),
})
