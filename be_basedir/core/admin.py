from django.contrib import admin

from .models import Building, Device, Room, ThresholdRule, ThresholdSettings


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at", "updated_at")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "building", "floor", "activity_label", "created_at")
    list_filter = ("building", "floor")
    search_fields = ("code", "name", "building__name", "building__code", "activity_label")
    ordering = ("building__code", "code")


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("device_id", "name", "device_type", "room", "is_active", "capacity_watt", "updated_at")
    list_filter = ("device_type", "is_active", "room__building")
    search_fields = ("device_id", "name", "room__name", "room__code")
    ordering = ("device_id",)


@admin.register(ThresholdRule)
class ThresholdRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "device", "room", "power_watt_gt", "severity", "is_enabled", "updated_at")
    list_filter = ("severity", "is_enabled")
    search_fields = ("name", "device__device_id", "room__code")


@admin.register(ThresholdSettings)
class ThresholdSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "daily_usage_limit_kwh",
        "peak_demand_watt",
        "budget_threshold_currency",
        "usage_spike_alert_percent",
        "updated_at",
    )
