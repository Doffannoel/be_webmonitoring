from __future__ import annotations

from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Building, Device, Room, ThresholdRule, ThresholdSettings
from monitoring.models import Alert, CarbonFootprint, EnergyPrediction, EnergyReading
from monitoring.services import evaluate_thresholds, update_daily_carbon_for_date


class Command(BaseCommand):
    help = "Seed dummy data for dashboard/frontend development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo data before seeding again.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="How many days of historical readings to generate.",
        )
        parser.add_argument(
            "--readings-per-device",
            type=int,
            default=3,
            help="How many readings to create per device per day.",
        )

    def handle(self, *args, **options):
        days = max(1, options["days"])
        readings_per_device = max(1, options["readings_per_device"])
        reset = options["reset"]

        if reset:
            self.stdout.write(self.style.WARNING("Reset mode enabled. Existing demo data will be deleted."))
        elif EnergyReading.objects.exists():
            self.stdout.write(
                self.style.WARNING("Demo data already exists. Use --reset to clear and regenerate it.")
            )
            return

        with transaction.atomic():
            if reset:
                self._clear_seed_data()

            buildings = self._seed_buildings()
            rooms = self._seed_rooms(buildings)
            devices = self._seed_devices(rooms)
            self._seed_threshold_settings()
            self._seed_threshold_rules(devices, rooms)
            self._seed_readings(devices, days=days, readings_per_device=readings_per_device)
            self._seed_predictions(days=14)
            self._seed_manual_alerts(devices)

        self.stdout.write(self.style.SUCCESS("Demo data berhasil dibuat."))
        self.stdout.write(
            f"Buildings: {Building.objects.count()}, Rooms: {Room.objects.count()}, Devices: {Device.objects.count()}, "
            f"Readings: {EnergyReading.objects.count()}, Alerts: {Alert.objects.count()}, Predictions: {EnergyPrediction.objects.count()}"
        )
        self.stdout.write(
            "Jalankan frontend lalu pakai endpoint API yang sudah ada; data dummy sekarang sudah tersedia."
        )

    def _clear_seed_data(self):
        Alert.objects.all().delete()
        CarbonFootprint.objects.all().delete()
        EnergyPrediction.objects.all().delete()
        EnergyReading.objects.all().delete()
        ThresholdRule.objects.all().delete()
        ThresholdSettings.objects.all().delete()
        Device.objects.all().delete()
        Room.objects.all().delete()
        Building.objects.all().delete()

    def _seed_buildings(self):
        building_specs = [
            ("BLD-ENG", "Engineering Building"),
            ("BLD-ADM", "Administration Building"),
            ("BLD-LAB", "Laboratory Building"),
        ]

        buildings = {}
        for code, name in building_specs:
            buildings[code], _ = Building.objects.update_or_create(
                code=code,
                defaults={"name": name},
            )
        return buildings

    def _seed_rooms(self, buildings):
        room_specs = [
            ("BLD-ENG", "ENG-101", "Engineering Hall A", "1", "Lecture"),
            ("BLD-ENG", "ENG-102", "Engineering Hall B", "1", "Lecture"),
            ("BLD-ENG", "ENG-201", "Engineering Lab", "2", "Practical"),
            ("BLD-ADM", "ADM-101", "Administration Office", "1", "Office"),
            ("BLD-ADM", "ADM-201", "Meeting Room", "2", "Meeting"),
            ("BLD-LAB", "LAB-301", "IoT Lab", "3", "Research"),
        ]

        rooms = {}
        for building_code, code, name, floor, activity_label in room_specs:
            building = buildings[building_code]
            rooms[code], _ = Room.objects.update_or_create(
                building=building,
                code=code,
                defaults={
                    "name": name,
                    "floor": floor,
                    "activity_label": activity_label,
                },
            )
        return rooms

    def _seed_devices(self, rooms):
        device_specs = [
            ("MTR-ENG-01", "Main Meter Engineering", "meter", "ENG-101", "", "", 5000),
            ("AC-ENG-01", "AC Hall A", "ac", "ENG-101", "1", "Lecture", 3500),
            ("LGT-ENG-01", "Lighting Hall B", "light", "ENG-102", "1", "Lecture", 300),
            ("CMP-ENG-01", "Lab Workstation Cluster", "computer", "ENG-201", "2", "Practical", 900),
            ("PMP-ADM-01", "Water Pump", "pump", "ADM-101", "1", "Office", 1200),
            ("AC-ADM-01", "Meeting Room AC", "ac", "ADM-201", "2", "Meeting", 2400),
            ("MTR-LAB-01", "Lab Meter", "meter", "LAB-301", "3", "Research", 4000),
            ("CMP-LAB-01", "IoT Lab Desktop", "computer", "LAB-301", "3", "Research", 650),
        ]

        devices = {}
        for device_id, name, device_type, room_code, floor_label, activity_label, capacity_watt in device_specs:
            room = rooms[room_code]
            devices[device_id], _ = Device.objects.update_or_create(
                device_id=device_id,
                defaults={
                    "name": name,
                    "device_type": device_type,
                    "room": room,
                    "floor_label": floor_label,
                    "activity_label": activity_label,
                    "brand": "DemoTech",
                    "model": f"DT-{device_id[-2:]}",
                    "capacity_watt": capacity_watt,
                    "is_active": True,
                },
            )
        return devices

    def _seed_threshold_settings(self):
        settings, _ = ThresholdSettings.objects.update_or_create(
            pk=1,
            defaults={
                "daily_usage_limit_kwh": 14.0,
                "peak_demand_watt": 3200.0,
                "budget_threshold_currency": 1500.0,
                "usage_spike_alert_percent": 25.0,
            },
        )
        return settings

    def _seed_threshold_rules(self, devices, rooms):
        rule_specs = [
            ("Critical AC spike", {"device": devices["AC-ENG-01"], "power_watt_gt": 2800.0, "severity": "critical"}),
            ("Meeting room warning", {"room": rooms["ADM-201"], "power_watt_gt": 1800.0, "severity": "warning"}),
            ("Lab warning", {"room": rooms["LAB-301"], "power_watt_gt": 2200.0, "severity": "warning"}),
            ("Pump notice", {"device": devices["PMP-ADM-01"], "power_watt_gt": 1000.0, "severity": "info"}),
        ]

        for name, defaults in rule_specs:
            ThresholdRule.objects.update_or_create(
                name=name,
                defaults={**defaults, "is_enabled": True},
            )

    def _seed_readings(self, devices, days: int, readings_per_device: int):
        timezone_obj = timezone.get_current_timezone()
        end_day = timezone.localdate()
        start_day = end_day - timedelta(days=days - 1)

        slot_times = [
            time(7, 0),
            time(13, 0),
            time(19, 0),
            time(22, 0),
        ]

        for offset in range(days):
            current_day = start_day + timedelta(days=offset)

            for device_index, device in enumerate(devices.values()):
                for slot_index in range(readings_per_device):
                    slot = slot_times[slot_index % len(slot_times)]
                    timestamp = timezone.make_aware(datetime.combine(current_day, slot), timezone_obj)
                    power_watt = self._power_watt_for(device.device_type, offset, slot_index, device_index)
                    energy_kwh = round(power_watt / 1000 * (0.35 + (slot_index * 0.05)), 3)
                    voltage = 220.0 if device.device_type != "meter" else 230.0
                    current = round(power_watt / voltage, 2) if voltage else None

                    reading = EnergyReading.objects.create(
                        device=device,
                        timestamp=timestamp,
                        voltage=voltage,
                        current=current,
                        power_watt=power_watt,
                        energy_kwh=energy_kwh,
                    )

                    evaluate_thresholds(
                        device=device,
                        power_watt=reading.power_watt,
                        reading_date=reading.timestamp.date(),
                    )

            update_daily_carbon_for_date(current_day)

    def _seed_predictions(self, days: int = 14):
        end_day = timezone.localdate()
        total_days = max(7, days)

        for offset in range(total_days):
            target_day = end_day + timedelta(days=offset + 1)
            base = 24.0 + (offset * 1.3)
            swing = 4.5 if offset % 4 else 11.0
            predicted_kwh = round(base + swing, 2)

            EnergyPrediction.objects.update_or_create(
                date=target_day,
                model_version="demo-v1",
                defaults={
                    "predicted_kwh": predicted_kwh,
                    "ci_low": round(predicted_kwh - 3.2, 2),
                    "ci_high": round(predicted_kwh + 3.8, 2),
                },
            )

    def _seed_manual_alerts(self, devices):
        now = timezone.now()
        manual_alerts = [
            {
                "device": devices["AC-ENG-01"],
                "alert_type": "demo_notice",
                "severity": "info",
                "message": "Demo data siap dipakai untuk dashboard frontend.",
                "is_resolved": True,
                "resolved_at": now,
                "timestamp": now - timedelta(hours=6),
            },
            {
                "device": devices["MTR-LAB-01"],
                "alert_type": "maintenance",
                "severity": "warning",
                "message": "Perlu cek kalibrasi meter lab untuk periode demo.",
                "is_resolved": False,
                "resolved_at": None,
                "timestamp": now - timedelta(hours=3),
            },
        ]

        for alert_data in manual_alerts:
            Alert.objects.update_or_create(
                device=alert_data["device"],
                alert_type=alert_data["alert_type"],
                message=alert_data["message"],
                defaults={
                    "severity": alert_data["severity"],
                    "is_resolved": alert_data["is_resolved"],
                    "resolved_at": alert_data["resolved_at"],
                    "timestamp": alert_data["timestamp"],
                },
            )

    def _power_watt_for(self, device_type: str, day_index: int, slot_index: int, device_index: int):
        base_map = {
            "meter": 1300,
            "ac": 2200,
            "light": 160,
            "computer": 420,
            "pump": 880,
            "other": 300,
        }
        base = base_map.get(device_type, 300)

        daily_wave = ((day_index % 6) - 2) * 45
        slot_wave = [0, 180, 320, -80][slot_index % 4]
        device_wave = (device_index % 3) * 55
        spike = 650 if device_type == "ac" and slot_index == 2 and day_index % 5 == 0 else 0
        spike += 500 if device_type == "pump" and slot_index == 1 and day_index % 7 == 0 else 0

        value = base + daily_wave + slot_wave + device_wave + spike
        return float(max(50, value))
