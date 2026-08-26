from .base import *  # noqa: F401,F403
from .base import BASE_DIR

DEBUG = False
SECRET_KEY = 'django-insecure-test-key'
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

# Hashes rápidos: los tests no necesitan seguridad real de passwords.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
