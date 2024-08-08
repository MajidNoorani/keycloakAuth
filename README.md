# keycloak Authentication and Authorization Module

Use this module as a submodule in your project

## Installation
Install all the required packages which are in [requirements.txt](requirements.txt)

## Setup and Configuration

you need to add these codes in proper directories:

1. <your_project>/<your_project_main_app>/settings.py
```
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    '<your_keycloakAuth_app_name>.keycloakAuth',
    ...
]

# Rest Framework settings
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
    ],
    'DEFAULT_PARSER_CLASSES': [
       'rest_framework.parsers.FormParser',
       'rest_framework.parsers.MultiPartParser',
       'rest_framework.parsers.JSONParser',
    ],
}

# drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'Daycare APIs',
    'DESCRIPTION': 'API documentation for Daycare',
    'VERSION': '1.0.0',
    'COMPONENT_SPLIT_REQUEST': True
}

```
Also we need to configure django to make it possible to make connection to keycloak.
So we add these configurations too:
```
KEYCLOAK_SERVER_URL = os.environ.get("KEYCLOAK_SERVER_URL", default='https://keycloak.domain.com')
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", default='<YourRealm>')
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", default='<YourClient>')
KEYCLOAK_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", default='changeme')
KEYCLOAK_REDIRECT_URI = os.environ.get("KEYCLOAK_REDIRECT_URI", default='http://domain.com/api/keycloak-auth/callback')
FRONT_URL = os.environ.get("FRONT_URL", default="https://domain.com")  # front url of the project
```


2. <your_project>/<your_project_main_app>/urls.py
```
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='api-schema'),
        name='api-docs'
        ),
    path('api/keycloak-auth/', include('<your_keycloakAuth_app_name>.keycloakAuth.urls')),
]

```

**Note**

You need to change the name of the app in [apps.py](keycloakAuth/apps.py) if you change the name of the app (By default the name of the app is set **keycloakUs**)

3. Migrate to apply changes on database
```
python manage.py migrate
```
4. In any view of your apis that you want authentication, add this line of code:
```
from rest_framework.authentication import TokenAuthentication
from <your_keycloakAuth_app_name>.keycloakAuth import authentication

...

authentication_classes = [TokenAuthentication]
permission_classes = [authentication.IsKeycloakAuthenticated]


```
5. Configure your keycloak and setup a **Realm** and a **Client**. Be aware that you need to enable credentials for your client to get the client secret from it.


**Note**

in your Django models, you cannot use a foreign key to users. Since this module is developed for a modular monolithic architecure, you can save the user id that keycloak gives you (**sub**) in your models to find the relation between your users and records in any model.
## Get new updates

```
git fetch origin
git merge origin/master
```

then resolve any conflict

## Fetching submodules in main project
After clonning the main project you need to use this command to get submodules too:
```
git submodule update
```