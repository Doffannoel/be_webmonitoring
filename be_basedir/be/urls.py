from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def home(request):
    return JsonResponse({
        "message": "Energy Monitoring API",
        "docs": "/api/docs/",
        "schema": "/api/schema/",
    })

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    path("api/auth/", include("users.urls")),
    path("api/core/", include("core.urls")),
    path("api/monitoring/", include("monitoring.urls")),
]