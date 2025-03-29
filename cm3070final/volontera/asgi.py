"""
ASGI config for volontera project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
import environ
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

env = environ.Env()
#if added for fly.io deployment
if os.environ.get("FLY_MACHINE_ID") is None:
    environ.Env.read_env(os.path.join(os.path.dirname(__file__), ".env"))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "volontera.settings.prod" if env("DJANGO_ENV", default="development") == "production" else "volontera.settings.dev"
)

django_asgi_app = get_asgi_application()

import accounts_notifs.routing
import chats.routing

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                accounts_notifs.routing.websocket_urlpatterns + chats.routing.websocket_urlpatterns
            )
        )
    )
})
