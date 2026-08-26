from .base import *  # noqa: F401,F403
from .base import env_db, env_list

DEBUG = False

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS')  # sin default: falla explícito si falta

DATABASES = {
    'default': env_db('DATABASE_URL'),  # sin default: falla explícito si falta
}

# CORS_ALLOWED_ORIGINS ya viene de base.py (env var), nunca ALLOW_ALL acá.

# Dominios completos con esquema (https://mi-app.up.railway.app) que pueden
# hacer POST autenticado por sesión — necesario para que /admin/ funcione
# detrás del proxy TLS de Railway/Render. La API vía JWT no lo necesita.
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', default=[])

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Static servido por whitenoise (sin CDN delante en Railway/Render). Se pisa
# solo acá porque exige el manifest de `collectstatic`, que dev/test nunca corren.
STORAGES = {
    'default': {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# Railway/Render leen logs de stdout/stderr; sin esto un 500 no deja rastro
# (el handler console default de Django se desactiva con DEBUG=False).
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.smtp.EmailBackend'}}
