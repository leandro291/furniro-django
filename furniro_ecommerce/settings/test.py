import tempfile

from .base import *  # noqa: F401,F403
from .base import BASE_DIR

DEBUG = False
SECRET_KEY = 'django-insecure-test-key-not-for-real-use-32bytes'
ALLOWED_HOSTS = ['*']

# Nunca pegarle a Cloudinary real desde un test: filesystem local en un dir temporal.
MEDIA_ROOT = tempfile.mkdtemp(prefix='furniro-test-media-')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

# Hashes rápidos: los tests no necesitan seguridad real de passwords.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}}
