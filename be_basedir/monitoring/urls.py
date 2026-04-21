from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AlertViewSet, AnalyticsViewSet, CarbonFootprintViewSet, EnergyPredictionViewSet, EnergyReadingViewSet

router = DefaultRouter()
router.register(r"readings", EnergyReadingViewSet, basename="readings")
router.register(r"carbon", CarbonFootprintViewSet, basename="carbon")
router.register(r"alerts", AlertViewSet, basename="alerts")
router.register(r"predictions", EnergyPredictionViewSet, basename="predictions")
router.register(r"analytics", AnalyticsViewSet, basename="analytics")

urlpatterns = [
    path("", include(router.urls)),
]
