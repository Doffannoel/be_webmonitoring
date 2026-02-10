from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import BuildingViewSet, RoomViewSet, DeviceViewSet, ThresholdRuleViewSet

router = DefaultRouter()
router.register(r"buildings", BuildingViewSet, basename="buildings")
router.register(r"rooms", RoomViewSet, basename="rooms")
router.register(r"devices", DeviceViewSet, basename="devices")
router.register(r"threshold-rules", ThresholdRuleViewSet, basename="threshold-rules")

urlpatterns = [
    path("", include(router.urls)),
]
