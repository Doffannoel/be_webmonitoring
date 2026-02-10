from django.db.models import Sum
from django.utils import timezone
from datetime import date
from .models import CarbonFootprint, Alert
from core.models import ThresholdRule

def update_daily_carbon_for_date(target_date: date, emission_factor: float = 0.80):
    # total_kwh dari EnergyReading hari itu
    from .models import EnergyReading  

    start = timezone.datetime.combine(target_date, timezone.datetime.min.time()).replace(tzinfo=timezone.get_current_timezone())
    end = timezone.datetime.combine(target_date, timezone.datetime.max.time()).replace(tzinfo=timezone.get_current_timezone())

    total = EnergyReading.objects.filter(timestamp__range=(start, end)).aggregate(s=Sum("energy_kwh"))["s"] or 0.0

    obj, _ = CarbonFootprint.objects.get_or_create(date=target_date)
    obj.total_kwh = float(total)
    obj.emission_factor = float(emission_factor)
    obj.save()
    return obj


def evaluate_thresholds(device, power_watt: float | None):
    if power_watt is None:
        return

    rules = ThresholdRule.objects.filter(is_enabled=True).filter(device=device) | ThresholdRule.objects.filter(is_enabled=True, device__isnull=True, room=device.room)

    for rule in rules.distinct():
        if rule.power_watt_gt is not None and power_watt > rule.power_watt_gt:
            Alert.objects.create(
                device=device,
                alert_type="threshold",
                severity=rule.severity,
                message=f"Power tinggi: {power_watt}W melebihi threshold {rule.power_watt_gt}W (rule: {rule.name})"
            )
