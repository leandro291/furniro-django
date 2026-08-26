from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS')  # sin default: falla explícito si falta

DATABASES = {
    'default': env.db('DATABASE_URL'),  # sin default: falla explícito si falta
}

# CORS_ALLOWED_ORIGINS ya viene de base.py (env var), nunca ALLOW_ALL acá.

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.smtp.EmailBackend'}}
