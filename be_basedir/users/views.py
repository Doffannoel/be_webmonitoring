from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    SignupSerializer,
    UserSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List users",
        description="Mengambil daftar user. Endpoint ini hanya bisa diakses oleh user yang sudah login.",
        responses={200: UserSerializer(many=True)},
        tags=["Auth / Users"],
    ),
)
class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get current user profile",
        description="Mengambil data profile user yang sedang login.",
        responses={200: UserSerializer},
        tags=["Auth / Users"],
    )
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="me")
    def me(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update current user profile",
        description="Update profile user yang sedang login. Field yang umum diubah: first_name, last_name, email.",
        request=UserSerializer,
        responses={200: UserSerializer},
        tags=["Auth / Users"],
        examples=[
            OpenApiExample(
                "Update profile request",
                value={
                    "first_name": "Budi",
                    "last_name": "Santoso",
                    "email": "budi@example.com",
                },
                request_only=True,
            )
        ],
    )
    @action(detail=False, methods=["patch"], permission_classes=[IsAuthenticated], url_path="me")
    def update_profile(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="User signup",
        description="Mendaftarkan user baru lalu mengembalikan access token, refresh token, dan data user.",
        request=SignupSerializer,
        responses={
            201: OpenApiResponse(description="Signup berhasil"),
            400: OpenApiResponse(description="Validasi gagal"),
        },
        tags=["Auth / Users"],
        examples=[
            OpenApiExample(
                "Signup request",
                value={
                    "username": "budi",
                    "email": "budi@example.com",
                    "password": "Password123!",
                    "first_name": "Budi",
                    "last_name": "Santoso",
                },
                request_only=True,
            )
        ],
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="signup")
    def signup(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        login_serializer = LoginSerializer(
            data={
                "username": request.data.get("username"),
                "password": request.data.get("password"),
            }
        )
        login_serializer.is_valid(raise_exception=True)

        return Response(
            {
                "message": "Signup berhasil.",
                "tokens": login_serializer.validated_data,
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="User logout",
        description="Logout user dengan memasukkan refresh token agar token tersebut diblacklist.",
        request=LogoutSerializer,
        responses={
            205: OpenApiResponse(description="Logout berhasil"),
            400: OpenApiResponse(description="Request tidak valid"),
        },
        tags=["Auth / Users"],
        examples=[
            OpenApiExample(
                "Logout request",
                value={
                    "refresh": "your_refresh_token_here"
                },
                request_only=True,
            )
        ],
    )
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="logout")
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Logout berhasil."},
            status=status.HTTP_205_RESET_CONTENT,
        )


@extend_schema(
    summary="User login",
    description="Login menggunakan username dan password, lalu mendapatkan access token dan refresh token.",
    request=LoginSerializer,
    responses={200: OpenApiResponse(description="Login berhasil")},
    tags=["Auth / Users"],
    examples=[
        OpenApiExample(
            "Login request",
            value={
                "username": "budi",
                "password": "Password123!",
            },
            request_only=True,
        )
    ],
)
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


@extend_schema(
    summary="Refresh JWT token",
    description="Menggunakan refresh token untuk mendapatkan access token baru.",
    responses={200: OpenApiResponse(description="Token berhasil direfresh")},
    tags=["Auth / Users"],
    examples=[
        OpenApiExample(
            "Refresh token request",
            value={
                "refresh": "your_refresh_token_here"
            },
            request_only=True,
        )
    ],
)
class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]