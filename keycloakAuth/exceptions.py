from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from keycloak.exceptions import KeycloakPostError, KeycloakAuthenticationError
from rest_framework import status


class KeycloakBaseView(GenericAPIView):
    """
    Base view for Keycloak-related operations.
    """
    def handle_keycloak_error(self, error: Exception) -> Response:
        """
        Centralized error handling for Keycloak-related errors.
        """
        if isinstance(error, KeycloakPostError):
            return Response(
                {'detail': "Invalid grant or token."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        elif isinstance(error, KeycloakAuthenticationError):
            return Response(
                {'detail': 'Authentication failed.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        else:
            return Response(
                {'detail': 'An unexpected error occurred',
                 'error': str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
