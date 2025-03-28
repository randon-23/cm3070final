from .base import *

DEBUG = False

ALLOWED_HOSTS = ['volontera.app.com', '35.228.239.164']
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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

# Use Redis for Channels Layer in Production
# Override the default Channels Layer configuration in base.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env("REDIS_HOST"), 6379)],  # Redis Cloud Host - GOOGLE MEMORY STORE
        },
    },
}
CELERY_BROKER_URL = env("CELERY_BROKER_URL")  # Example: redis://prod-redis-server:6379/0
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")  # Example: redis://prod-redis-server:6379/0

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# STATIC_URL = 'https://storage.googleapis.com/YOUR_BUCKET_NAME/static/'
# MEDIA_URL = 'https://storage.googleapis.com/YOUR_BUCKET_NAME/media/'