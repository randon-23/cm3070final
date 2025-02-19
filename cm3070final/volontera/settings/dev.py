from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cm3070final',
        'USER': 'postgres_user',
        'PASSWORD': 'postgrespassword',
        'HOST': '127.0.0.1', # localhost
        'PORT': '5432'
    }
}