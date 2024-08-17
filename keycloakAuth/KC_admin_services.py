from keycloak import KeycloakOpenIDConnection, KeycloakAdmin
from django.conf import settings
from typing import Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)
# Configure client

keycloak_connection = KeycloakOpenIDConnection(
                        server_url=settings.KEYCLOAK_SERVER_URL,
                        username=settings.KEYCLOAK_ADMIN,
                        password=settings.KEYCLOAK_ADMIN_PASSWORD,
                        realm_name="master",
                        user_realm_name=settings.KEYCLOAK_REALM,
                        client_id=settings.KEYCLOAK_CLIENT_ID,
                        client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
                        verify=True
                        )

keycloak_admin = KeycloakAdmin(connection=keycloak_connection)


def create_user(
    email: str,
    username: str,
    firstName: str,
    lastname: str,
    enabled: True,
    password: str
):
    # it is possible to add locale and other attributes too
    new_user = keycloak_admin.create_user(
        {"email": email,
         "username": username,
         "enabled": enabled,
         "firstName": firstName,
         "lastName": lastname,
         "credentials": [{"value": password, "type": "password"}]},
        exist_ok=False
    )
    return new_user


def count_users():
    count_users = keycloak_admin.users_count()
    return count_users


def filter_users(query: Optional[dict] = None):
    users = keycloak_admin.get_users(query)
    return users


def get_userid_by_username(username: str):
    return keycloak_admin.get_user_id(username)


def get_user_by_id(user_id: str):
    return keycloak_admin.get_user(user_id)


def ensure_user_id(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        username = kwargs.get('username')
        user_id = kwargs.get('user_id')

        if username is None and user_id is None:
            raise ValueError(
                "At least one of 'username' or 'user_id' must be provided.")

        if not user_id and username:
            kwargs['user_id'] = get_userid_by_username(username)

        return func(*args, **kwargs)

    return wrapper


@ensure_user_id
def update_user(username: Optional[str] = None,
                user_id: Optional[str] = None,
                **kwargs):
    # Call the keycloak_admin.update_user with user_id and payload
    response = keycloak_admin.update_user(
        user_id=user_id,
        payload=kwargs
    )
    return response


@ensure_user_id
def update_user_password(password: str,
                         username: Optional[str] = None,
                         user_id: Optional[str] = None,
                         temporary: bool = False):

    response = keycloak_admin.set_user_password(user_id=user_id,
                                                password=password,
                                                temporary=temporary)
    return response


@ensure_user_id
def get_user_credentials(username: Optional[str] = None,
                         user_id: Optional[str] = None):

    credentials = keycloak_admin.get_credentials(user_id=user_id)
    return credentials


@ensure_user_id
def delete_user_credential(credential_id: str,
                           username: Optional[str] = None,
                           user_id: Optional[str] = None):

    response = keycloak_admin.delete_credential(user_id=user_id,
                                                credential_id=credential_id)
    return response


@ensure_user_id
def delete_user(username: Optional[str] = None,
                user_id: Optional[str] = None):

    response = keycloak_admin.delete_user(user_id=user_id)
    return response


@ensure_user_id
def get_consents_granted_by_user(username: Optional[str] = None,
                                 user_id: Optional[str] = None):

    consents = keycloak_admin.consents_user(user_id=user_id)
    return consents


@ensure_user_id
def send_update_account(payload: list = ['UPDATE_PASSWORD'],
                        username: Optional[str] = None,
                        user_id: Optional[str] = None):

    response = keycloak_admin.send_update_account(user_id=user_id,
                                                  payload=payload)
    return response


@ensure_user_id
def send_verify_email(username: Optional[str] = None,
                      user_id: Optional[str] = None):

    response = keycloak_admin.send_verify_email(user_id=user_id)
    return response


@ensure_user_id
def get_sessions(username: Optional[str] = None,
                 user_id: Optional[str] = None):

    response = keycloak_admin.get_sessions(user_id=user_id)
    return response
