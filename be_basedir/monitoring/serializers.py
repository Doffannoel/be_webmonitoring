from rest_framework import serializers

from .models import Alert, CarbonFootprint, EnergyPrediction, EnergyReading


class EnergyReadingSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source="device.device_id", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True)
    room_name = serializers.CharField(source="device.room.name", read_only=True)
    building_code = serializers.CharField(source="device.room.building.code", read_only=True)
    floor = serializers.SerializerMethodField()
    activity = serializers.SerializerMethodField()
    device_type = serializers.CharField(source="device.device_type", read_only=True)

    class Meta:
        model = EnergyReading
        fields = "__all__"

    def get_floor(self, obj):
        return obj.device.floor_label or (obj.device.room.floor if obj.device.room else "")

    def get_activity(self, obj):
        return obj.device.activity_label or (obj.device.room.activity_label if obj.device.room else "")


class CarbonFootprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarbonFootprint
        fields = "__all__"


class AlertSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source="device.device_id", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True)

    class Meta:
        model = Alert
        fields = "__all__"


class EnergyPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergyPrediction
        fields = "__all__"
