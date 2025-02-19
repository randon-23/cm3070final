"""
WSGI config for volontera project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import environ
from django.core.wsgi import get_wsgi_application

env = environ.Env()
environ.Env.read_env(os.path.join(os.path.dirname(__file__), '.env'))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "volontera.settings.prod" if env("DJANGO_ENV", default="development") == "production" else "volontera.settings.dev"
)

application = get_wsgi_application()
