from django.conf import settings
from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from urllib.parse import urlencode
from . import KC_openID_services
from . import serializers
from .authentication import IsKeycloakAuthenticated
from rest_framework import status, viewsets, mixins
from keycloak.exceptions import (
    KeycloakPostError,
    KeycloakAuthenticationError
)
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import UserProfile
from django.utils import timezone
from rest_framework.parsers import MultiPartParser
from django.http.response import HttpResponseRedirect



class KeycloakLoginView(GenericAPIView):
    """Redirects to Keycloak login page."""

    def get_serializer_class(self):
        return None

    def get(self, request, *args, **kwargs):
        keycloak_auth_url = \
            f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth"  # noqa
        params = {
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'response_type': 'code',
            'scope': 'openid email profile',
            'redirect_uri': settings.KEYCLOAK_REDIRECT_URI,
        }
        url = f"{keycloak_auth_url}?{urlencode(params)}"
        print(url)
        return redirect(url)


class KeycloakCallbackView(GenericAPIView):
    """Called by Keycloak."""
    serializer_class = serializers.TokenSerializer

    def get(self, request, *args, **kwargs):
        code = request.GET.get('code')
        if not code:
            return Response({'error': 'Missing code parameter'}, status=400)

        try:
            # Get token
            tokens = KC_openID_services.get_access_token_with_code(code)
            # Serialize the token data
            serializer = self.get_serializer(data={
                'access_token': tokens['access_token'],
                'expires_in': tokens['expires_in'],
                'refresh_token': tokens['refresh_token'],
                'refresh_expires_in': tokens['refresh_expires_in'],
                'token_type': tokens['token_type']
            })

            if serializer.is_valid():
                response = HttpResponseRedirect(redirect_to=settings.BASE_FRONTEND_URL)

                cookie_max_age = 3600  # 60 minutes
                for key, value in serializer.validated_data.items():
                    response.set_cookie(
                        key=key,
                        value=value,
                        max_age=cookie_max_age,
                        # httponly=True,
                        secure=True,
                        samesite='Lax',
                        domain=f'.{settings.BASE_FRONTEND_URL.split("//")[1]}',
                        # path='/'
                    )

                return response
            else:
                return Response(serializer.errors, status=400)
        except KeycloakPostError:
            return Response(
                {'detail': "Invalid grant. Code is not valid."},
                status=status.HTTP_401_UNAUTHORIZED
                 )
        except Exception as e:
            # Handle other exceptions
            return Response(
                {'detail': 'An unexpected error occurred', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class RefreshTokenView(GenericAPIView):
    """Refresh access token by passing refresh token."""
    serializer_class = serializers.RefreshTokenRequestSerializer

    @extend_schema(
        summary="Refresh Token",
        responses={
            204: OpenApiResponse(response=serializers.RefreshTokenSerializer),
        },
    )
    def post(self, request, *args, **kwargs):
        # Validate incoming data using RefreshTokenRequestSerializer
        request_serializer = self.serializer_class(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        refresh_token = request_serializer.validated_data.get('refresh_token')

        try:
            # Call service to get new tokens
            tokens = KC_openID_services.get_refresh_token(refresh_token)
            # Serialize the response data
            response_serializer = serializers.RefreshTokenSerializer(data={
                'access_token': tokens['access_token'],
                'expires_in': tokens['expires_in'],
                'refresh_token': tokens['refresh_token'],
                'refresh_expires_in': tokens['refresh_expires_in'],
                'token_type': tokens['token_type']
            })
            if response_serializer.is_valid():
                return Response(response_serializer.data)
            else:
                return Response(response_serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        except KeycloakPostError:
            return Response(
                {'detail': "Invalid grant. Token is not active."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            # Handle other exceptions
            return Response(
                {'detail': 'An unexpected error occurred', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateUserView(GenericAPIView):
    """Redirects user to keycloak for profile update."""
    def get_serializer_class(self):
        return None

    def get(self, request, *args, **kwargs):
        keycloak_change_password_url = \
            f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/account"  # noqa
        return redirect(keycloak_change_password_url)


class UserInfoView(GenericAPIView):
    """Get authenticated user information."""
    serializer_class = serializers.UserInfoSerializer
    permission_classes = [IsKeycloakAuthenticated]

    # authentication_classes = [authentication.KeycloakAuthentication,]

    def get(self, request, *args, **kwargs):
        user_info = request.user
        serializer = self.get_serializer(data=user_info)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=400)


class LogOutView(GenericAPIView):
    """Logs out the user."""
    serializer_class = serializers.LogoutSerializer

    @extend_schema(
        summary="Logout with refresh token",
        responses={
            204: OpenApiResponse(description="User logged out successfully"),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            refresh_token = serializer.validated_data.get('refresh_token')
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            KC_openID_services.logout(refresh_token)
            return Response({"detail": "User logged out successfully."},
                            status=status.HTTP_204_NO_CONTENT)

        except KeycloakPostError:
            return Response(
                    {'detail': "Invalid grant. Token is invalid."},
                    status=status.HTTP_401_UNAUTHORIZED
                    )
        except Exception as e:
            # Handle other exceptions
            return Response(
                {'detail': 'An unexpected error occurred',
                    'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class SimpleLoginView(GenericAPIView):
    """Get authenticated user information."""

    serializer_class = serializers.SimpleLoginSerializer

    @extend_schema(
        summary="Login with username and password",
        responses={
            200: OpenApiResponse(response=serializers.TokenSerializer),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            username_or_email = serializer.validated_data.get(
                'username_or_email')
            password = serializer.validated_data.get('password')
            totp = serializer.validated_data.get('totp', None)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            tokens = KC_openID_services.get_token_with_user_and_pass(
                username_or_email,
                password,
                totp)
            response_serializer = serializers.TokenSerializer(data={
                'access_token': tokens['access_token'],
                'expires_in': tokens['expires_in'],
                'refresh_token': tokens['refresh_token'],
                'refresh_expires_in': tokens['refresh_expires_in'],
                'token_type': tokens['token_type']
            })
            if response_serializer.is_valid():
                return Response(response_serializer.data)
            else:
                return Response(response_serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        except KeycloakAuthenticationError:
            return Response(
                {'detail': 'Username or Password not correct!'},
                status=status.HTTP_401_UNAUTHORIZED
                )
        except Exception as e:
            # Handle other exceptions
            return Response(
                {'detail': 'An unexpected error occurred', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class UserProfileView(mixins.CreateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    """View for manage user profile side fields"""
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [IsKeycloakAuthenticated]
    parser_classes = [MultiPartParser]
    queryset = UserProfile.objects.all()

    def perform_create(self, serializer):
        """Create a new Comment"""
        serializer.save(uuid=self.request.user['sub'],
                        email=self.request.user['email'])

    def perform_update(self, serializer):
        """Create a new Comment"""
        serializer.save(updatedDate=timezone.now())
