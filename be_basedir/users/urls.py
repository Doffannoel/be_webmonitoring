from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LoginView, RefreshView, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/signin/", LoginView.as_view(), name="auth_signin"),
    path("auth/token/", LoginView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", RefreshView.as_view(), name="token_refresh"),
    path("auth/signup/", UserViewSet.as_view({"post": "signup"}), name="auth_signup"),
    path("auth/me/", UserViewSet.as_view({"get": "me", "patch": "update_profile"}), name="auth_me"),
    path("auth/signout/", UserViewSet.as_view({"post": "logout"}), name="auth_signout"),
]
