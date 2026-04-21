from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Building, Device, Room, ThresholdSettings
from monitoring.models import EnergyReading


class MonitoringTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="password123")
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        self.building = Building.objects.create(name="Gedung A", code="A")
        self.room = Room.objects.create(building=self.building, name="Ruang 101", code="101", floor="1")
        self.device = Device.objects.create(device_id="DEV-001", name="Meter 1", room=self.room, device_type="meter")
        ThresholdSettings.objects.get_or_create(pk=1)

    def test_ingest_and_daily_series(self):
        ingest_resp = self.client.post(
            "/monitoring/readings/ingest/",
            {"device_id": "DEV-001", "power_watt": 1000, "energy_kwh": 10},
            format="json",
        )
        self.assertEqual(ingest_resp.status_code, 201)
        self.assertEqual(EnergyReading.objects.count(), 1)

        analytics_resp = self.client.get("/monitoring/analytics/daily-series/")
        self.assertEqual(analytics_resp.status_code, 200)
        self.assertIn("results", analytics_resp.data)
