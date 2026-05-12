from django.contrib.auth.models import User
from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Building, Device, Room, ThresholdRule, ThresholdSettings
from monitoring.models import Alert, EnergyReading


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class MonitoringTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            password="password123",
            email="tester@example.com",
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        self.building = Building.objects.create(name="Gedung A", code="A")
        self.room = Room.objects.create(building=self.building, name="Ruang 101", code="101", floor="1")
        self.device = Device.objects.create(
            device_id="DEV-001",
            name="Meter 1",
            room=self.room,
            device_type="meter",
            user=self.user,
        )
        ThresholdSettings.objects.get_or_create(pk=1)

    def test_ingest_and_daily_series(self):
        ingest_resp = self.client.post(
            "/api/monitoring/readings/ingest/",
            {"device_id": "DEV-001", "power_watt": 1000, "energy_kwh": 10},
            format="json",
        )
        self.assertEqual(ingest_resp.status_code, 201)
        self.assertEqual(EnergyReading.objects.count(), 1)

        analytics_resp = self.client.get("/api/monitoring/analytics/daily-series/")
        self.assertEqual(analytics_resp.status_code, 200)
        self.assertIn("results", analytics_resp.data)

    def test_threshold_alert_sends_email_to_device_owner(self):
        ThresholdRule.objects.create(
            name="High Power",
            device=self.device,
            power_watt_gt=500,
            severity="critical",
            is_enabled=True,
        )

        ingest_resp = self.client.post(
            "/api/monitoring/readings/ingest/",
            {"device_id": "DEV-001", "power_watt": 800, "energy_kwh": 2},
            format="json",
        )

        self.assertEqual(ingest_resp.status_code, 201)
        self.assertEqual(Alert.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Meter 1", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["tester@example.com"])
