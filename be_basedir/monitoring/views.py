from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import date

from .models import EnergyReading, CarbonFootprint, Alert, EnergyPrediction
from .serializers import (
    EnergyReadingSerializer,
    CarbonFootprintSerializer,
    AlertSerializer,
    EnergyPredictionSerializer,
)

from core.models import Device
from .services import update_daily_carbon_for_date, evaluate_thresholds


class EnergyReadingViewSet(viewsets.ModelViewSet):
    queryset = EnergyReading.objects.select_related("device", "device__room", "device__room__building").all()
    serializer_class = EnergyReadingSerializer
    filterset_fields = ["device", "device__room", "device__room__building"]
    search_fields = ["device__device_id", "device__name"]
    ordering_fields = ["timestamp", "power_watt", "energy_kwh"]

    @action(detail=False, methods=["post"], url_path="ingest")
    def ingest(self, request):
        """
        IoT kirim data minimal:
        - device_id (string)
        - timestamp (optional, ISO; kalau kosong pakai now)
        - voltage/current/power_watt/energy_kwh optional
        """
        device_id = request.data.get("device_id")
        if not device_id:
            return Response({"detail": "device_id wajib"}, status=status.HTTP_400_BAD_REQUEST)

        device = Device.objects.filter(device_id=device_id).first()
        if not device:
            return Response({"detail": f"Device {device_id} tidak ditemukan"}, status=status.HTTP_404_NOT_FOUND)

        ts = request.data.get("timestamp")
        timestamp = timezone.now() if not ts else ts

        payload = {
            "device": device.id,
            "timestamp": timestamp,
            "voltage": request.data.get("voltage"),
            "current": request.data.get("current"),
            "power_watt": request.data.get("power_watt"),
            "energy_kwh": request.data.get("energy_kwh"),
        }

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        reading = serializer.save()

        # update carbon harian
        update_daily_carbon_for_date(reading.timestamp.date())

        # evaluate alert rules
        evaluate_thresholds(device=device, power_watt=reading.power_watt)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CarbonFootprintViewSet(viewsets.ModelViewSet):
    queryset = CarbonFootprint.objects.all()
    serializer_class = CarbonFootprintSerializer
    filterset_fields = ["date"]
    ordering_fields = ["date", "total_kwh", "emission_kg_co2"]

    @action(detail=False, methods=["post"], url_path="recalc")
    def recalc(self, request):
        target_date = request.data.get("date")
        if not target_date:
            target_date = date.today().isoformat()
        d = date.fromisoformat(target_date)
        obj = update_daily_carbon_for_date(d)
        return Response(CarbonFootprintSerializer(obj).data)


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.select_related("device").all()
    serializer_class = AlertSerializer
    filterset_fields = ["severity", "is_resolved", "device"]
    search_fields = ["message", "device__device_id"]
    ordering_fields = ["timestamp", "severity"]

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        return Response(self.get_serializer(alert).data)


class EnergyPredictionViewSet(viewsets.ModelViewSet):
    queryset = EnergyPrediction.objects.all()
    serializer_class = EnergyPredictionSerializer
    filterset_fields = ["date", "model_version"]
    ordering_fields = ["date", "predicted_kwh"]
