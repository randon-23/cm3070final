from .base import *
import dj_database_url

DEBUG = False
SITE_ID=3
ALLOWED_HOSTS = ['volontera.fly.dev', 'localhost', '127.0.0.1']
MEDIA_ROOT = os.path.join('/app', 'media')

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=False)
}
# Use Redis for Channels Layer in Production
# Override the default Channels Layer configuration in base.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env("REDIS_URL"))],  # Redis Cloud Host - GOOGLE MEMORY STORE
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

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# STATIC_URL = 'https://storage.googleapis.com/YOUR_BUCKET_NAME/static/'
# MEDIA_URL = 'https://storage.googleapis.com/YOUR_BUCKET_NAME/media/'