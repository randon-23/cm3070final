# Celery configuration file
import os
import environ

from celery import Celery

env = environ.Env()
environ.Env.read_env(os.path.join(os.path.dirname(__file__), ".env"))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "volontera.settings.prod" if env("DJANGO_ENV", default="development") == "production" else "volontera.settings.dev"
)

# Celery configuration
app=Celery('volontera')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()