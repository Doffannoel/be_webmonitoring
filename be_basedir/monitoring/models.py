from django.db import models
from django.utils import timezone
from core.models import Device

class EnergyReading(models.Model):
    """
    Time-series dari IoT:
    timestamp, device_id, voltage, current, power, energy_kwh (sesuai proposal). :contentReference[oaicite:2]{index=2}
    """
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="readings")
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    voltage = models.FloatField(null=True, blank=True)
    current = models.FloatField(null=True, blank=True)
    power_watt = models.FloatField(null=True, blank=True)
    energy_kwh = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["device", "timestamp"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.device.device_id} @ {self.timestamp}"


class CarbonFootprint(models.Model):
    """
    Perhitungan jejak karbon:
    date, total_kwh, emission_factor, emission_kg_co2
    Proposal menyinggung faktor emisi standar (contoh JAMALI 0.80 kgCO2/kWh). :contentReference[oaicite:3]{index=3}
    """
    date = models.DateField(unique=True)
    total_kwh = models.FloatField(default=0.0)
    emission_factor = models.FloatField(default=0.80)
    emission_kg_co2 = models.FloatField(default=0.0)

    def recalc(self):
        self.emission_kg_co2 = float(self.total_kwh) * float(self.emission_factor)

    def save(self, *args, **kwargs):
        self.recalc()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.emission_kg_co2:.2f} kgCO2"


class Alert(models.Model):
    SEVERITY = [("info", "Info"), ("warning", "Warning"), ("critical", "Critical")]

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")

    alert_type = models.CharField(max_length=50, default="threshold")
    severity = models.CharField(max_length=10, choices=SEVERITY, default="warning")
    message = models.TextField()

    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.severity}] {self.message[:40]}"


class EnergyPrediction(models.Model):
    """
    Hasil forecasting (nanti AI/ML belakangan):
    date, predicted_kwh, confidence_interval, model_version (sesuai proposal). :contentReference[oaicite:4]{index=4}
    """
    date = models.DateField(db_index=True)
    predicted_kwh = models.FloatField()
    ci_low = models.FloatField(null=True, blank=True)
    ci_high = models.FloatField(null=True, blank=True)

    model_version = models.CharField(max_length=50, default="v0")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("date", "model_version")]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} pred={self.predicted_kwh} ({self.model_version})"
