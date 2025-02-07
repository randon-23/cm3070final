"""
ASGI config for volontera project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
import environ
from django.core.asgi import get_asgi_application

env = environ.Env()
environ.Env.read_env(os.path.join(os.path.dirname(__file__), ".env"))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "volontera.settings.prod" if env("DJANGO_ENV", default="development") == "production" else "volontera.settings.dev"
)

application = get_asgi_application()
