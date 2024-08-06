from django.urls import path, include
from .views import (
    KeycloakLoginView,
    KeycloakCallbackView,
    UpdateUserView,
    UserInfoView,
    RefreshTokenView,
    LogOutView,
    SimpleLoginView,
    UserProfileView
)
from rest_framework.routers import DefaultRouter

urlpatterns = [
     path('login/',
          KeycloakLoginView.as_view(),
          name='keycloak_login'),
     path('callback/',
          KeycloakCallbackView.as_view(),
          name='keycloak_callback'),
     path('update-user/',
          UpdateUserView.as_view(),
          name='keycloak_update_user'),
     path('user-info/',
          UserInfoView.as_view(),
          name='user_info'),
     path('refresh-token/',
          RefreshTokenView.as_view(),
          name='refresh_token'),
     path('logout/',
          LogOutView.as_view(),
          name='logout'),
     path('simple-login/',
          SimpleLoginView.as_view(),
          name='simple_login'),
]

router = DefaultRouter()
router.register('user-profile', UserProfileView)

app_name = 'kc_auth'

urlpatterns += [
    path('', include(router.urls))
]
