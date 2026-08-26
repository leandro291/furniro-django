from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Más agresivo que el throttle anónimo global: mitiga fuerza bruta en login."""

    scope = 'login'
