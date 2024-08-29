from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from . import kc_openID_services
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.permissions import BasePermission


class KeycloakAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        access_token = auth_header.split()[1]
        try:
            userinfo = kc_openID_services.get_user_info(access_token)
            user = KeycloakUser(userinfo)
            return (user, None)
        except:
            raise AuthenticationFailed(
                "Incorrect authentication credentials. Either the authentication token is not valid or expired."
            )


class KeycloakAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'keycloakAuth.keycloakAuth.authentication.KeycloakAuthentication'
    name = 'BearerAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }


class IsKeycloakAuthenticated(BasePermission):
    def has_permission(self, request, view):
        # Perform token validation and permissions checks
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return False

        access_token = auth_header.split()[1]

        try:
            userinfo = kc_openID_services.get_user_info(access_token)
            # Add additional permission checks if needed
            return True
        except:
            return False


class KeycloakUser:
    def __init__(self, userinfo):
        self.userinfo = userinfo

    @property
    def is_authenticated(self):
        return True

    def __getattr__(self, item):
        return self.userinfo.get(item, None)
