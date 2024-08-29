from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .kc_openID_services import get_token_with_user_and_pass, decode_token
from django.conf import settings


class KeycloakBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            tokens = get_token_with_user_and_pass(username, password)
            user = decode_token(tokens["access_token"])
            if user is None:
                return None  # Authentication failed

            django_user = self.get_or_create_user(user)
            return django_user  # Return only the user object

        except PermissionError as e:
            # You can log the error or use Django messages to display it
            if request is not None:
                from django.contrib import messages
                messages.error(request, str(e))
            return None

        except Exception as e:
            # Log the unexpected error or handle it appropriately
            if request is not None:
                from django.contrib import messages
                messages.error(
                    request, "An unexpected error occurred: " + str(e))
            return None

    def get_or_create_user(self, keycloak_user):
        User = get_user_model()
        django_user, created = User.objects.get_or_create(
            username=keycloak_user["preferred_username"],
            defaults={
                'email': keycloak_user["email"],
                'first_name': keycloak_user["given_name"],
                'last_name': keycloak_user["family_name"],
            }
        )

        if not created:
            django_user.email = keycloak_user["email"]
            django_user.first_name = keycloak_user["given_name"]
            django_user.last_name = keycloak_user["family_name"]

        roles = keycloak_user.get("resource_access", {}).get(settings.KEYCLOAK_CLIENT_ID, {}).get("roles", [])  # noqa
        if 'superuser' in roles:
            django_user.is_superuser = True
            django_user.is_staff = True
        elif 'staff' in roles:
            django_user.is_staff = True
        else:
            django_user.is_staff = False
            django_user.is_superuser = False
            raise PermissionError(
                "You are not permitted to log in as an admin")

        django_user.save()
        return django_user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
