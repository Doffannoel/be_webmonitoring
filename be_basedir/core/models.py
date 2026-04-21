from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Building(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Room(TimeStampedModel):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=30)
    floor = models.CharField(max_length=50, blank=True, default="")
    activity_label = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        unique_together = [("building", "code")]

    def __str__(self):
        return f"{self.building.code}/{self.code} - {self.name}"


class Device(TimeStampedModel):
    DEVICE_TYPES = [
        ("meter", "Energy Meter"),
        ("ac", "Air Conditioner"),
        ("light", "Lighting"),
        ("computer", "Computer"),
        ("pump", "Pump"),
        ("other", "Other"),
    ]

    device_id = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default="meter")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="devices")
    floor_label = models.CharField(max_length=50, blank=True, default="")
    activity_label = models.CharField(max_length=100, blank=True, default="")
    brand = models.CharField(max_length=100, blank=True, null=True, default="")
    model = models.CharField(max_length=100, blank=True, null=True, default="")
    capacity_watt = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.device_id} - {self.name}"


class ThresholdRule(TimeStampedModel):
    SEVERITY = [("info", "Info"), ("warning", "Warning"), ("critical", "Critical")]

    name = models.CharField(max_length=120)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name="threshold_rules")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name="threshold_rules")
    power_watt_gt = models.FloatField(null=True, blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY, default="warning")
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        scope = self.device.device_id if self.device else (self.room.code if self.room else "global")
        return f"{self.name} ({scope})"


class ThresholdSettings(TimeStampedModel):
    daily_usage_limit_kwh = models.FloatField(default=50.0)
    peak_demand_watt = models.FloatField(default=5000.0)
    budget_threshold_currency = models.FloatField(default=1000.0)
    usage_spike_alert_percent = models.FloatField(default=20.0)

    class Meta:
        verbose_name_plural = "Threshold Settings"

    def __str__(self):
        return "Global Threshold Settings"
