from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import EnergyReadingViewSet, CarbonFootprintViewSet, AlertViewSet, EnergyPredictionViewSet

router = DefaultRouter()
router.register(r"readings", EnergyReadingViewSet, basename="readings")
router.register(r"carbon", CarbonFootprintViewSet, basename="carbon")
router.register(r"alerts", AlertViewSet, basename="alerts")
router.register(r"predictions", EnergyPredictionViewSet, basename="predictions")

urlpatterns = [
    path("", include(router.urls)),
]
