"""
ASGI config for furniro_ecommerce project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os
from pathlib import Path

from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'furniro_ecommerce.settings.development')

application = get_asgi_application()
