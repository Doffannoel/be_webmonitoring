from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Building, Device, Room, ThresholdRule, ThresholdSettings
from .serializers import (
    BuildingSerializer,
    DeviceSerializer,
    RoomSerializer,
    ThresholdRuleSerializer,
    ThresholdSettingsSerializer,
)


class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all().order_by("code")
    serializer_class = BuildingSerializer
    search_fields = ["name", "code"]
    ordering_fields = ["code", "name"]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related("building").all().order_by("building__code", "code")
    serializer_class = RoomSerializer
    filterset_fields = ["building", "floor", "activity_label"]
    search_fields = ["name", "code", "building__name", "building__code", "floor", "activity_label"]
    ordering_fields = ["code", "name", "floor"]


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.select_related("room", "room__building").all().order_by("device_id")
    serializer_class = DeviceSerializer
    filterset_fields = ["device_type", "is_active", "room", "room__building", "floor_label", "activity_label"]
    search_fields = ["device_id", "name", "room__name", "room__code", "floor_label", "activity_label"]
    ordering_fields = ["device_id", "name", "updated_at"]


class ThresholdRuleViewSet(viewsets.ModelViewSet):
    queryset = ThresholdRule.objects.select_related("device", "room").all().order_by("-updated_at")
    serializer_class = ThresholdRuleSerializer
    filterset_fields = ["severity", "is_enabled", "device", "room"]
    search_fields = ["name", "device__device_id", "room__code"]
    ordering_fields = ["updated_at", "severity"]


class ThresholdSettingsViewSet(viewsets.ModelViewSet):
    queryset = ThresholdSettings.objects.all().order_by("id")
    serializer_class = ThresholdSettingsSerializer

    def list(self, request, *args, **kwargs):
        obj, _ = ThresholdSettings.objects.get_or_create(pk=1)
        return Response(self.get_serializer(obj).data)

    def create(self, request, *args, **kwargs):
        obj, _ = ThresholdSettings.objects.get_or_create(pk=1)
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get", "patch"], url_path="current")
    def current(self, request):
        obj, _ = ThresholdSettings.objects.get_or_create(pk=1)
        if request.method.lower() == "get":
            return Response(self.get_serializer(obj).data)

        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
