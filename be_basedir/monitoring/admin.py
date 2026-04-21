from django.contrib import admin

from .models import Alert, CarbonFootprint, EnergyPrediction, EnergyReading


@admin.register(EnergyReading)
class EnergyReadingAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "device", "power_watt", "energy_kwh", "voltage", "current")
    list_filter = ("device", "device__room__building")
    search_fields = ("device__device_id", "device__name")
    ordering = ("-timestamp",)


@admin.register(CarbonFootprint)
class CarbonFootprintAdmin(admin.ModelAdmin):
    list_display = ("date", "total_kwh", "emission_factor", "emission_kg_co2")
    ordering = ("-date",)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "severity", "alert_type", "device", "is_resolved")
    list_filter = ("severity", "is_resolved", "alert_type")
    search_fields = ("message", "device__device_id")


@admin.register(EnergyPrediction)
class EnergyPredictionAdmin(admin.ModelAdmin):
    list_display = ("date", "predicted_kwh", "ci_low", "ci_high", "model_version", "created_at")
    list_filter = ("model_version",)
    ordering = ("-date",)
