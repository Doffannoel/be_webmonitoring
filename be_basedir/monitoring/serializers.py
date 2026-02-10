from rest_framework import serializers
from .models import EnergyReading, CarbonFootprint, Alert, EnergyPrediction

class EnergyReadingSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source="device.device_id", read_only=True)

    class Meta:
        model = EnergyReading
        fields = "__all__"

class CarbonFootprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarbonFootprint
        fields = "__all__"

class AlertSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source="device.device_id", read_only=True)

    class Meta:
        model = Alert
        fields = "__all__"

class EnergyPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergyPrediction
        fields = "__all__"
