from pathlib import Path
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent # One level further up from the original path since the 
# destructured settings.py is now a directory

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('DJANGO_SECRET_KEY')
SITE_ID=2
#ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=["localhost"])

INSTALLED_APPS = [
    # Third party apps
    'rest_framework',
    'channels',
    'daphne',
    'drf_yasg',
    'address',
    'phonenumber_field',
    'django_celery_beat',
    # Default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    # Custom apps
    'accounts_notifs.apps.AccountsNotifsConfig',
    'base.apps.BaseConfig',
    'chats.apps.ChatsConfig',
    'opportunities_engagements.apps.OpportunitiesEngagementsConfig',
    'volunteers_organizations.apps.VolunteersOrganizationsConfig',
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'volontera.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'volunteers_organizations.context_processors.google_places_api_key'
            ],
        },
    },
]

WSGI_APPLICATION = 'volontera.wsgi.application'
ASGI_APPLICATION = 'volontera.asgi.application'

# Channels Layer Configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"  # Default for local testing
    }
}

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default="redis://127.0.0.1:6379/0")  # Default to Redis (override for prod)
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default="redis://127.0.0.1:6379/1")  # Default to Redis (override for prod)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'accounts_notifs.validators.UserPasswordValidator'
    }
]

# Overrod built-in user model and implemented Custom user model
AUTH_USER_MODEL = 'accounts_notifs.Account'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend'
]

# Django Allauth configurations
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = False # Disable auto sign up with social accounts due to custom sign up process
SOCIALACCOUNT_LOGIN_ON_GET = True

# Email configurations
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

# Google Social Account configurations - removed ['APP'] key from the dictionary as was defined in Django admin
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
SOCIALACCOUNT_ADAPTER = 'accounts_notifs.adapters.GoogleSocialAccountAdapter'
# Redirect after login/logout
LOGIN_REDIRECT_URL = 'volunteers_organizations:profile'
LOGOUT_REDIRECT_URL = 'home' # Redirect to home page after logout


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

GOOGLE_API_KEY=env('GOOGLE_API_KEY')
GOOGLE_PLACES_API_KEY=env('GOOGLE_PLACES_API_KEY')

# Logging - Console logging for development and production environment
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'chats': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
