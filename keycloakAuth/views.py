# Standard library imports
from urllib.parse import urlencode
from typing import Dict, Any

# Django imports
from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from django.http import HttpResponseRedirect

# Rest framework imports
from rest_framework.response import Response
from rest_framework import status, viewsets, mixins
from rest_framework.parsers import MultiPartParser

# Third-party imports
from drf_spectacular.utils import extend_schema, OpenApiResponse


# Local imports
from . import kc_openID_services
from . import serializers
from .authentication import IsKeycloakAuthenticated
from .models import UserProfile
from .exceptions import KeycloakBaseView


class KeycloakLoginView(KeycloakBaseView):
    """
    View to redirect users to the Keycloak login page.
    """
    @extend_schema(
        summary="Redirect to Keycloak Login",
        responses={302: None},
    )
    def get(self, request, *args, **kwargs):
        """
        Construct the Keycloak authentication URL and redirect the user.
        """
        keycloak_auth_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/auth"  # noqa
        params = {
            'client_id': settings.KEYCLOAK_CLIENT_ID,
            'response_type': 'code',
            'scope': 'openid email profile',
            'redirect_uri': settings.KEYCLOAK_REDIRECT_URI,
        }
        url = f"{keycloak_auth_url}?{urlencode(params)}"
        return redirect(url)


class KeycloakCallbackView(KeycloakBaseView):
    """
    View to handle the callback from Keycloak after successful authentication.
    """
    serializer_class = serializers.TokenSerializer

    @extend_schema(
        summary="Keycloak Callback",
        responses={
            302: None,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Process the authentication code and set tokens in cookies.
        """
        code = request.GET.get('code')
        if not code:
            return Response(
                {'error': 'Missing code parameter'},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            tokens = kc_openID_services.get_access_token_with_code(code)
            serializer = self.get_serializer(data=tokens)
            if serializer.is_valid():
                response = HttpResponseRedirect(
                    redirect_to=settings.BASE_FRONTEND_URL)
                self._set_token_cookies(response, serializer.validated_data)
                return response
            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self.handle_keycloak_error(e)

    def _set_token_cookies(self,
                           response: HttpResponseRedirect,
                           token_data: Dict[str, Any]) -> None:
        """
        Set token data in secure cookies.
        """
        cookie_max_age = 3600  # 60 minutes
        for key, value in token_data.items():
            response.set_cookie(
                key=key,
                value=value,
                max_age=cookie_max_age,
                secure=True,
                httponly=True,
                samesite='Lax',
                domain=f'.{settings.BASE_FRONTEND_URL.split("//")[1]}',
            )


class RefreshTokenView(KeycloakBaseView):
    """
    View to refresh the access token using a refresh token.
    """
    serializer_class = serializers.RefreshTokenRequestSerializer

    @extend_schema(
        summary="Refresh Token",
        responses={
            200: OpenApiResponse(response=serializers.RefreshTokenSerializer),
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Refresh the access token using the provided refresh token.
        """
        request_serializer = self.get_serializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                request_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        refresh_token = request_serializer.validated_data.get('refresh_token')

        try:
            tokens = kc_openID_services.get_refresh_token(refresh_token)
            response_serializer = serializers.RefreshTokenSerializer(
                data=tokens
                )
            if response_serializer.is_valid():
                return Response(response_serializer.data)
            else:
                return Response(
                    response_serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self.handle_keycloak_error(e)


class UserInfoView(KeycloakBaseView):
    """
    View to retrieve authenticated user information.
    """
    serializer_class = serializers.UserInfoSerializer
    permission_classes = [IsKeycloakAuthenticated]

    @extend_schema(
        summary="Get User Info",
        responses={
            200: OpenApiResponse(response=serializers.UserInfoSerializer),
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve and return the authenticated user's information.
        """
        user_info = request.user
        serializer = self.get_serializer(data=user_info)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)


class LogOutView(KeycloakBaseView):
    """
    View to log out the user by invalidating their refresh token.
    """
    serializer_class = serializers.LogoutSerializer

    @extend_schema(
        summary="Logout",
        responses={
            204: OpenApiResponse(description="User logged out successfully"),
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Log out the user by invalidating their refresh token.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        refresh_token = serializer.validated_data.get('refresh_token')
        try:
            kc_openID_services.logout(refresh_token)
            return Response(
                {"detail": "User logged out successfully."},
                status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return self.handle_keycloak_error(e)


class SimpleLoginView(KeycloakBaseView):
    """
    View for user login with username/email and password.
    """
    serializer_class = serializers.SimpleLoginSerializer

    @extend_schema(
        summary="Login with username and password",
        responses={
            200: OpenApiResponse(response=serializers.TokenSerializer),
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Authenticate user with username/email and password,
        optionally using TOTP.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        username_or_email = serializer.validated_data.get('username_or_email')
        password = serializer.validated_data.get('password')
        totp = serializer.validated_data.get('totp')

        try:
            tokens = kc_openID_services.get_token_with_user_and_pass(
                username_or_email,
                password,
                totp)
            response_serializer = serializers.TokenSerializer(
                data=tokens)
            if response_serializer.is_valid():
                return Response(response_serializer.data)
            else:
                return Response(
                    response_serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self.handle_keycloak_error(e)


class UserProfileViewSet(mixins.CreateModelMixin,
                         mixins.DestroyModelMixin,
                         mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    """
    ViewSet for managing user profile-related operations.
    """
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [IsKeycloakAuthenticated]
    parser_classes = [MultiPartParser]
    queryset = UserProfile.objects.all()

    def perform_create(self, serializer):
        """
        Create a new user profile, associating it with the authenticated user.
        """
        serializer.save(
            uuid=self.request.user['sub'],
            email=self.request.user['email'])

    def perform_update(self, serializer):
        """
        Update an existing user profile, recording the update time.
        """
        serializer.save(updatedDate=timezone.now())
