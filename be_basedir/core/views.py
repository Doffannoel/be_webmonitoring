from rest_framework import viewsets
from .models import Building, Room, Device, ThresholdRule
from .serializers import BuildingSerializer, RoomSerializer, DeviceSerializer, ThresholdRuleSerializer

class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    search_fields = ["name", "code"]
    ordering_fields = ["code", "name"]

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related("building").all()
    serializer_class = RoomSerializer
    filterset_fields = ["building"]
    search_fields = ["name", "code", "building__name", "building__code"]
    ordering_fields = ["code", "name"]

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.select_related("room", "room__building").all()
    serializer_class = DeviceSerializer
    filterset_fields = ["device_type", "is_active", "room", "room__building"]
    search_fields = ["device_id", "name", "room__name", "room__code"]
    ordering_fields = ["device_id", "name", "updated_at"]

class ThresholdRuleViewSet(viewsets.ModelViewSet):
    queryset = ThresholdRule.objects.select_related("device", "room").all()
    serializer_class = ThresholdRuleSerializer
    filterset_fields = ["severity", "is_enabled", "device", "room"]
    search_fields = ["name", "device__device_id", "room__code"]
    ordering_fields = ["updated_at", "severity"]
