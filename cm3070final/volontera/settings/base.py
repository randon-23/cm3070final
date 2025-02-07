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
            ],
        },
    },
]

WSGI_APPLICATION = 'volontera.wsgi.application'
ASGI_APPLICATION = 'volontera.asgi.application'

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

# Redirect after login/logout
LOGIN_REDIRECT_URL = '/dashboard/' # Redirect to dashboard after login
LOGOUT_REDIRECT_URL = 'home' # Redirect to home page after logout

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

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

GOOGLE_API_KEY=env('GOOGLE_API_KEY')

# Logging - Console logging for development and production environment
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    },
    '__main__': {
        'handlers': ['console'],
        'level': 'WARNING',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
