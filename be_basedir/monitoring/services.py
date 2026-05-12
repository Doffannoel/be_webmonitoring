from datetime import date
import logging

from django.core.mail import send_mail
from django.db.models import Avg, Sum
from django.utils import timezone

from core.models import ThresholdRule, ThresholdSettings

from .models import Alert, CarbonFootprint

logger = logging.getLogger(__name__)


def send_alert_email(user_email: str, device_name: str, alert_type: str, severity: str, message: str):
    """
    Send alert notification email to user.
    
    Args:
        user_email: Email address of the user
        device_name: Name of the device
        alert_type: Type of alert (threshold, daily_usage_limit, peak_demand, etc)
        severity: Severity level (info, warning, critical)
        message: Alert message
    """
    if not user_email:
        return
    
    try:
        # Format email subject based on severity
        severity_prefix = {
            'critical': '⚠️ CRITICAL',
            'warning': '⚡ WARNING',
            'info': 'ℹ️ INFO'
        }
        prefix = severity_prefix.get(severity, 'Alert')
        
        subject = f"[{prefix}] Energy Alert: {device_name}"
        
        # Format email body
        email_body = f"""
Dear User,

An energy monitoring alert has been triggered:

Device: {device_name}
Alert Type: {alert_type.replace('_', ' ').title()}
Severity: {severity.upper()}
Message: {message}

Timestamp: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check your dashboard for more details and take necessary action.

---
Energy Monitoring System
"""
        
        send_mail(
            subject=subject,
            message=email_body,
            from_email=None,  # Will use DEFAULT_FROM_EMAIL
            recipient_list=[user_email],
            fail_silently=False,
        )
        logger.info(f"Alert email sent to {user_email} for device {device_name}")
    except Exception as e:
        logger.error(f"Failed to send alert email to {user_email}: {str(e)}")


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
        alert = Alert.objects.create(device=device, alert_type=alert_type, severity=severity, message=message)
        
        # Send email notification if device has an associated user with email
        if device.user and device.user.email:
            send_alert_email(
                user_email=device.user.email,
                device_name=device.name,
                alert_type=alert_type,
                severity=severity,
                message=message
            )


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
