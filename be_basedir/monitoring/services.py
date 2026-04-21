from datetime import date

from django.db.models import Avg, Sum
from django.utils import timezone

from core.models import ThresholdRule, ThresholdSettings

from .models import Alert, CarbonFootprint


def update_daily_carbon_for_date(target_date: date, emission_factor: float = 0.80):
    from .models import EnergyReading

    start = timezone.datetime.combine(target_date, timezone.datetime.min.time()).replace(
        tzinfo=timezone.get_current_timezone()
    )
    end = timezone.datetime.combine(target_date, timezone.datetime.max.time()).replace(
        tzinfo=timezone.get_current_timezone()
    )

    total = EnergyReading.objects.filter(timestamp__range=(start, end)).aggregate(s=Sum("energy_kwh"))["s"] or 0.0
    obj, _ = CarbonFootprint.objects.get_or_create(date=target_date)
    obj.total_kwh = float(total)
    obj.emission_factor = float(emission_factor)
    obj.save()
    return obj


def create_alert_if_missing(device, alert_type: str, severity: str, message: str):
    already_exists = Alert.objects.filter(
        device=device,
        alert_type=alert_type,
        message=message,
        is_resolved=False,
    ).exists()
    if not already_exists:
        Alert.objects.create(device=device, alert_type=alert_type, severity=severity, message=message)


def evaluate_thresholds(device, power_watt: float | None, reading_date=None):
    if power_watt is None:
        return

    room_rules = ThresholdRule.objects.filter(is_enabled=True, device__isnull=True, room=device.room)
    device_rules = ThresholdRule.objects.filter(is_enabled=True, device=device)

    for rule in (device_rules | room_rules).distinct():
        if rule.power_watt_gt is not None and power_watt > rule.power_watt_gt:
            create_alert_if_missing(
                device=device,
                alert_type="threshold",
                severity=rule.severity,
                message=f"Power {power_watt}W melebihi threshold {rule.power_watt_gt}W ({rule.name})",
            )

    settings, _ = ThresholdSettings.objects.get_or_create(pk=1)
    from .models import EnergyReading

    target_date = reading_date or timezone.localdate()
    day_qs = EnergyReading.objects.filter(device=device, timestamp__date=target_date)
    total_daily_kwh = day_qs.aggregate(total=Sum("energy_kwh"))["total"] or 0
    avg_power = day_qs.aggregate(avg=Avg("power_watt"))["avg"] or 0

    if total_daily_kwh > settings.daily_usage_limit_kwh:
        create_alert_if_missing(
            device=device,
            alert_type="daily_usage_limit",
            severity="warning",
            message=f"Pemakaian harian {total_daily_kwh:.2f} kWh melebihi limit {settings.daily_usage_limit_kwh:.2f} kWh",
        )

    if power_watt > settings.peak_demand_watt:
        create_alert_if_missing(
            device=device,
            alert_type="peak_demand",
            severity="critical",
            message=f"Peak demand {power_watt:.2f} W melebihi batas {settings.peak_demand_watt:.2f} W",
        )

    if avg_power and power_watt > avg_power * (1 + settings.usage_spike_alert_percent / 100):
        create_alert_if_missing(
            device=device,
            alert_type="usage_spike",
            severity="warning",
            message=(
                f"Lonjakan pemakaian: {power_watt:.2f} W di atas rata-rata {avg_power:.2f} W "
                f"lebih dari {settings.usage_spike_alert_percent:.2f}%"
            ),
        )
