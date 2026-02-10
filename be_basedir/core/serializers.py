from rest_framework import serializers
from .models import Building, Room, Device, ThresholdRule

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = "__all__"

class RoomSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source="building.name", read_only=True)
    building_code = serializers.CharField(source="building.code", read_only=True)

    class Meta:
        model = Room
        fields = "__all__"

class DeviceSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source="room.name", read_only=True)
    building_code = serializers.CharField(source="room.building.code", read_only=True)

    class Meta:
        model = Device
        fields = "__all__"

class ThresholdRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThresholdRule
        fields = "__all__"
