from keycloak import KeycloakOpenID
from django.conf import settings
# Configure client
# For versions older than 18 /auth/ must be added at the end of the server_url.
keycloak_openid = KeycloakOpenID(server_url=settings.KEYCLOAK_SERVER_URL,
                                 client_id=settings.KEYCLOAK_CLIENT_ID,
                                 realm_name=settings.KEYCLOAK_REALM,
                                 client_secret_key=settings.KEYCLOAK_CLIENT_SECRET,
                                 proxies={"http://": None, "https://": None, })


config_well_known = keycloak_openid.well_known()


def get_code():
    # Get code with OAuth authorization request
    auth_url = keycloak_openid.auth_url(
        redirect_uri=settings.CALLBACK_URL,
        scope="email",
        state="your_state_info")

    return auth_url


def get_access_token_with_code(code: str):
    """Get access token with code
    returns: {
        {
            "access_token": "access_token"
            "expires_in": 300,
            "refresh_expires_in": 1800,
            "refresh_token": "referesh_token",
            "token_type": "Bearer",
            "id_token": "id_token",
            "not-before-policy": 0,
            "session_state": "shashed_session_state",
            "scope": "openid email profile"
        }
    """
    tokens = keycloak_openid.token(
        grant_type='authorization_code',
        code=code,  # the_code_you_get_from_auth_url_callback
        redirect_uri=settings.KEYCLOAK_REDIRECT_URI
        )
    return tokens


def get_token_with_user_and_pass(user: str, password: str, totp: int = None):
    """
    Get access token with user and password


    Args:
        user (str): username or email
        password (str)
        totp (str): is a time based one-time password

    Returns:
        dict: A dictionary containing the token and some other fields.
            - access_token (hashed)
            - expires_in (int)
            - refresh_expires_in (int)
            - refresh_token (hashed)
            - token_type (str)
            - id_token (hashed)
            - not-before-policy (int)
            - session_state (hashed)
            - scope (str)
    """
    if totp:
        tokens = keycloak_openid.token(user, password, totp=totp)
        return tokens
    tokens = keycloak_openid.token(user, password)
    return tokens


def get_token_using_token_exchange(access_token):
    # Get token using Token Exchange¶
    return NotImplementedError
    tokens = keycloak_openid.exchange_token(
        access_token,
        "my_client",
        "other_client",
        "some_user")


def get_refresh_token(refresh_token):
    """
    Refresh token

    Args:
        token (str): The JWT token to decode.

    Returns:
        dict: A dictionary containing the token and some other fields.
            - access_token (hashed)
            - expires_in (int)
            - refresh_expires_in (int)
            - refresh_token (hashed)
            - token_type (str)
            - id_token (hashed)
            - not-before-policy (int)
            - session_state (hashed)
            - scope (str)
    """
    tokens = keycloak_openid.refresh_token(refresh_token)
    return tokens


def get_user_info(token):
    """
    Get UserInfo

    returns:
    {
        'sub': '1e7e3c89-2ed8-4f2d-9b9a-c3ed2fa666d4',
        'email_verified': True,
        'name': 'Majid Noorani',
        'preferred_username': 'majid94',
        'given_name': 'Majid',
        'family_name': 'Noorani',
        'email': 'majid.noorani94@gmail.com'}
    """
    userinfo = keycloak_openid.userinfo(token)
    return userinfo


def logout(refresh_token):
    """Logout"""
    keycloak_openid.logout(refresh_token)


def get_certs():
    # Get certs
    certs = keycloak_openid.certs()
    return certs


def get_introspect(access_token: str,
                   rpt: str,
                   token_type_hint: str = "requesting_party_token"):
    # Introspect RPT
    token_rpt_info = keycloak_openid.introspect(
        keycloak_openid.introspect(access_token,
                                   token_type_hint=None))
    return token_rpt_info


def get_introspect_token(access_token):
    # Introspect token
    token_info = keycloak_openid.introspect(access_token)
    return token_info


def decode_token(access_token,
                 validate: bool = True):
    """
    Decodes a JWT token issued by Keycloak.

    Args:
        token (str): The JWT token to decode.

    Returns:
        dict: A dictionary containing the decoded token claims.
            - exp (int): Expiration time in Unix epoch format.
            - iat (int): Issued at time in Unix epoch format.
            - auth_time (int): Authentication time in Unix epoch format.
            - jti (str): JWT ID, a unique identifier for the token.
            - iss (str): Issuer, typically the URL of the Keycloak server and realm.
            - aud (str): Audience, the intended recipient of the token.
            - sub (str): Subject, the unique identifier for the user.
            - typ (str): Type of the token, typically 'Bearer'.
            - azp (str): Authorized party, usually the client ID.
            - sid (str): Session ID, the ID of the session in which the token was issued.
            - acr (str): Authentication Context Class Reference, indicating the authentication level.
            - allowed-origins (list): Origins allowed to make requests using this token.
            - realm_access (dict): Roles assigned to the user in the realm.
            - resource_access (dict): Roles assigned to the user for specific clients.
            - scope (str): Scope of the access request.
            - email_verified (bool): Indicates if the user's email address is verified.
            - name (str): Full name of the user.
            - preferred_username (str): The username preferred by the user.
            - given_name (str): Given (first) name of the user.
            - family_name (str): Family (last) name of the user.
            - email (str): Email address of the user.
    """
    token_info = keycloak_openid.decode_token(access_token, validate=validate)
    return token_info


def get_uma_premissions(user: str,
                        password: str,
                        permissions: str = "Resource#Scope"):
    # Get UMA-permissions by token
    tokens = keycloak_openid.token(user, password)
    permissions = keycloak_openid.uma_permissions(tokens['access_token'],
                                                  permissions="Resource#Scope")
    return permissions


def auth_status(access_token: str):
    # Get auth status for a specific resource and scope by token
    auth_status = keycloak_openid.has_uma_access(access_token, "Resource#Scope")
    return auth_status
