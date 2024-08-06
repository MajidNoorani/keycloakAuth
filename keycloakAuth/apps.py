from django.apps import AppConfig
from . import authentication


class KeycloakAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'keycloakAuth.keycloakAuth'

    def ready(self):
        authentication.KeycloakAuthenticationScheme
