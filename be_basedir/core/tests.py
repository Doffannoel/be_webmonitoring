from django.test import SimpleTestCase

from .models import Building, Device, Room
from .serializers import DeviceSerializer


class DeviceSerializerTests(SimpleTestCase):
    def test_includes_building_name_for_device_with_room(self):
        building = Building(name="Main Building", code="MAIN")
        room = Room(building=building, name="Room 101", code="101")
        device = Device(device_id="METER-001", name="Energy Meter", room=room)

        data = DeviceSerializer(device).data

        self.assertEqual(data["building_name"], "Main Building")

    def test_building_name_is_null_for_device_without_room(self):
        device = Device(device_id="METER-002", name="Standalone Meter")

        data = DeviceSerializer(device).data

        self.assertIsNone(data["building_name"])
