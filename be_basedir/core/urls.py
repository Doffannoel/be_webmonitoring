from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BuildingViewSet,
    DeviceViewSet,
    RoomViewSet,
    ThresholdRuleViewSet,
    ThresholdSettingsViewSet,
)

router = DefaultRouter()
router.register(r"buildings", BuildingViewSet, basename="buildings")
router.register(r"rooms", RoomViewSet, basename="rooms")
router.register(r"devices", DeviceViewSet, basename="devices")
router.register(r"threshold-rules", ThresholdRuleViewSet, basename="threshold-rules")
router.register(r"threshold-settings", ThresholdSettingsViewSet, basename="threshold-settings")

urlpatterns = [
    path("", include(router.urls)),
]
