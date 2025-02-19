from .base import *

DEBUG = False

ALLOWED_HOSTS = ['volontera.app.com', '34.175.6.80']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env("DB_NAME"),
        'USER': env("DB_USER"),
        'PASSWORD': env("DB_PASSWORD"),
        'HOST': env("DB_HOST"),
        'PORT': "5432",
    }
}

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# STATIC_URL = 'https://storage.googleapis.com/YOUR_BUCKET_NAME/static/'
# MEDIA_URL = 'https://storage.googleapis.com/YOUR_BUCKET_NAME/media/'