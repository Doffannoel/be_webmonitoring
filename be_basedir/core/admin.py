from django.contrib import admin
from .models import Building, Room, Device, ThresholdRule

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at", "updated_at")
    search_fields = ("code", "name")
    ordering = ("code",)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "building", "created_at")
    list_filter = ("building",)
    search_fields = ("code", "name", "building__name", "building__code")
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
