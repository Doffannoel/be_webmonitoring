from rest_framework import serializers

from .models import Building, Device, Room, ThresholdRule, ThresholdSettings


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
    room_code = serializers.CharField(source="room.code", read_only=True)
    building_code = serializers.CharField(source="room.building.code", read_only=True)
    floor = serializers.SerializerMethodField()
    activity = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = "__all__"

    def get_floor(self, obj):
        return obj.floor_label or (obj.room.floor if obj.room else "")

    def get_activity(self, obj):
        return obj.activity_label or (obj.room.activity_label if obj.room else "")


class ThresholdRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThresholdRule
        fields = "__all__"


class ThresholdSettingsSerializer(serializers.ModelSerializer):
    dailyUsageLimit = serializers.FloatField(source="daily_usage_limit_kwh")
    peakDemand = serializers.FloatField(source="peak_demand_watt")
    budgetThreshold = serializers.FloatField(source="budget_threshold_currency")
    usageSpikeAlert = serializers.FloatField(source="usage_spike_alert_percent")

    class Meta:
        model = ThresholdSettings
        fields = (
            "id",
            "dailyUsageLimit",
            "peakDemand",
            "budgetThreshold",
            "usageSpikeAlert",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
