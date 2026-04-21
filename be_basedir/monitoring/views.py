from datetime import date, timedelta

from django.db.models import Avg, Count, F, Sum, Window
from django.db.models.functions import Coalesce, Lag, TruncDay, TruncMonth, TruncWeek
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Device
from .models import Alert, CarbonFootprint, EnergyPrediction, EnergyReading
from .serializers import (
    AlertSerializer,
    CarbonFootprintSerializer,
    EnergyPredictionSerializer,
    EnergyReadingSerializer,
)
from .services import evaluate_thresholds, update_daily_carbon_for_date


@extend_schema_view(
    list=extend_schema(
        summary="List energy readings",
        description="Ambil daftar energy readings dengan dukungan filter, search, dan ordering.",
        tags=["Monitoring / Readings"],
    ),
    retrieve=extend_schema(
        summary="Get energy reading detail",
        tags=["Monitoring / Readings"],
    ),
    create=extend_schema(
        summary="Create energy reading",
        description="Membuat energy reading manual dari backend/admin.",
        tags=["Monitoring / Readings"],
    ),
    update=extend_schema(
        summary="Update energy reading",
        tags=["Monitoring / Readings"],
    ),
    partial_update=extend_schema(
        summary="Partial update energy reading",
        tags=["Monitoring / Readings"],
    ),
    destroy=extend_schema(
        summary="Delete energy reading",
        tags=["Monitoring / Readings"],
    ),
)
class EnergyReadingViewSet(viewsets.ModelViewSet):
    queryset = EnergyReading.objects.select_related(
        "device",
        "device__room",
        "device__room__building",
    ).all()
    serializer_class = EnergyReadingSerializer
    filterset_fields = ["device", "device__room", "device__room__building", "device__device_type"]
    search_fields = ["device__device_id", "device__name"]
    ordering_fields = ["timestamp", "power_watt", "energy_kwh"]
    ordering = ["-timestamp"]

    @extend_schema(
        summary="Ingest energy reading",
        description="""
Endpoint untuk menerima data reading dari IoT device atau frontend.

Field request:
- device_id: string, wajib
- timestamp: datetime ISO8601, opsional
- voltage: float, opsional
- current: float, opsional
- power_watt: float, opsional
- energy_kwh: float, opsional

Side effects:
- update carbon footprint harian
- evaluate threshold rules dan generate alert jika perlu
""",
        request=None,
        responses={
            201: EnergyReadingSerializer,
            400: OpenApiResponse(description="device_id tidak dikirim / payload tidak valid"),
            404: OpenApiResponse(description="Device tidak ditemukan"),
        },
        tags=["Monitoring / Readings"],
        examples=[
            OpenApiExample(
                "Ingest payload",
                value={
                    "device_id": "AC-01",
                    "timestamp": "2025-04-25T10:30:00Z",
                    "voltage": 220.0,
                    "current": 5.2,
                    "power_watt": 1144.0,
                    "energy_kwh": 1.15,
                },
                request_only=True,
            )
        ],
    )
    @action(detail=False, methods=["post"], url_path="ingest")
    def ingest(self, request):
        device_id = request.data.get("device_id")
        if not device_id:
            return Response(
                {"detail": "device_id wajib diisi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device = Device.objects.filter(device_id=device_id).first()
        if not device:
            return Response(
                {"detail": f"Device dengan device_id '{device_id}' tidak ditemukan."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = {
            "device": device.id,
            "timestamp": request.data.get("timestamp") or timezone.now(),
            "voltage": request.data.get("voltage"),
            "current": request.data.get("current"),
            "power_watt": request.data.get("power_watt"),
            "energy_kwh": request.data.get("energy_kwh"),
        }

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        reading = serializer.save()

        update_daily_carbon_for_date(reading.timestamp.date())
        evaluate_thresholds(
            device=device,
            power_watt=reading.power_watt,
            reading_date=reading.timestamp.date(),
        )

        return Response(
            self.get_serializer(reading).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    list=extend_schema(
        summary="List carbon footprint data",
        tags=["Monitoring / Carbon"],
    ),
    retrieve=extend_schema(
        summary="Get carbon footprint detail",
        tags=["Monitoring / Carbon"],
    ),
    create=extend_schema(
        summary="Create carbon footprint record",
        tags=["Monitoring / Carbon"],
    ),
    update=extend_schema(
        summary="Update carbon footprint record",
        tags=["Monitoring / Carbon"],
    ),
    partial_update=extend_schema(
        summary="Partial update carbon footprint record",
        tags=["Monitoring / Carbon"],
    ),
    destroy=extend_schema(
        summary="Delete carbon footprint record",
        tags=["Monitoring / Carbon"],
    ),
)
class CarbonFootprintViewSet(viewsets.ModelViewSet):
    queryset = CarbonFootprint.objects.all().order_by("-date")
    serializer_class = CarbonFootprintSerializer
    filterset_fields = ["date"]
    ordering_fields = ["date", "total_kwh", "emission_kg_co2"]
    ordering = ["-date"]

    @extend_schema(
        summary="Recalculate daily carbon footprint",
        description="Hitung ulang carbon footprint untuk tanggal tertentu. Jika tanggal tidak dikirim, pakai hari ini.",
        request=None,
        responses={200: CarbonFootprintSerializer},
        tags=["Monitoring / Carbon"],
        examples=[
            OpenApiExample(
                "Recalc payload",
                value={"date": "2025-04-25"},
                request_only=True,
            )
        ],
    )
    @action(detail=False, methods=["post"], url_path="recalc")
    def recalc(self, request):
        target_date = request.data.get("date") or date.today().isoformat()
        obj = update_daily_carbon_for_date(date.fromisoformat(target_date))
        return Response(CarbonFootprintSerializer(obj).data)


@extend_schema_view(
    list=extend_schema(
        summary="List alerts",
        description="Ambil daftar alert. Bisa difilter berdasarkan severity, status resolve, device, dan alert_type.",
        tags=["Monitoring / Alerts"],
    ),
    retrieve=extend_schema(
        summary="Get alert detail",
        tags=["Monitoring / Alerts"],
    ),
    create=extend_schema(
        summary="Create alert",
        tags=["Monitoring / Alerts"],
    ),
    update=extend_schema(
        summary="Update alert",
        tags=["Monitoring / Alerts"],
    ),
    partial_update=extend_schema(
        summary="Partial update alert",
        description="""
Frontend bisa resolve alert dengan:
- PATCH /alerts/{id}/ { "is_resolved": true }
Jika `resolved_at` belum ada, backend akan otomatis mengisi timestamp sekarang.
""",
        tags=["Monitoring / Alerts"],
    ),
    destroy=extend_schema(
        summary="Delete alert",
        tags=["Monitoring / Alerts"],
    ),
)
class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.select_related("device", "device__room", "device__room__building").all()
    serializer_class = AlertSerializer
    filterset_fields = ["severity", "is_resolved", "device", "alert_type"]
    ordering_fields = ["timestamp", "severity", "resolved_at"]
    ordering = ["-timestamp"]

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()

        should_resolve = str(data.get("is_resolved", "")).lower() in {"1", "true", "yes"}
        should_unresolve = str(data.get("is_resolved", "")).lower() in {"0", "false", "no"}

        if should_resolve and not instance.resolved_at:
            data["resolved_at"] = data.get("resolved_at") or timezone.now()

        if should_unresolve:
            data["resolved_at"] = None

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        summary="Resolve alert",
        description="Resolve alert secara eksplisit via action endpoint.",
        responses={200: AlertSerializer},
        tags=["Monitoring / Alerts"],
    )
    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save(update_fields=["is_resolved", "resolved_at"])
        return Response(self.get_serializer(alert).data)

    @extend_schema(
        summary="Unresolve alert",
        description="Mengembalikan alert ke status belum resolved.",
        responses={200: AlertSerializer},
        tags=["Monitoring / Alerts"],
    )
    @action(detail=True, methods=["post"], url_path="unresolve")
    def unresolve(self, request, pk=None):
        alert = self.get_object()
        alert.is_resolved = False
        alert.resolved_at = None
        alert.save(update_fields=["is_resolved", "resolved_at"])
        return Response(self.get_serializer(alert).data)


@extend_schema_view(
    list=extend_schema(summary="List energy predictions", tags=["Monitoring / Predictions"]),
    retrieve=extend_schema(summary="Get energy prediction detail", tags=["Monitoring / Predictions"]),
    create=extend_schema(summary="Create energy prediction", tags=["Monitoring / Predictions"]),
    update=extend_schema(summary="Update energy prediction", tags=["Monitoring / Predictions"]),
    partial_update=extend_schema(summary="Partial update energy prediction", tags=["Monitoring / Predictions"]),
    destroy=extend_schema(summary="Delete energy prediction", tags=["Monitoring / Predictions"]),
)
class EnergyPredictionViewSet(viewsets.ModelViewSet):
    queryset = EnergyPrediction.objects.all()
    serializer_class = EnergyPredictionSerializer
    filterset_fields = ["date", "model_version"]
    ordering_fields = ["date", "predicted_kwh"]
    ordering = ["-date"]

    @extend_schema(
        summary="Prediction trends",
        description="Ambil 7 prediksi terbaru untuk kebutuhan trend chart.",
        tags=["Monitoring / Predictions"],
    )
    @action(detail=False, methods=["get"], url_path="trends")
    def trends(self, request):
        predictions = self.queryset.order_by("-date")[:7]
        data = [{"date": p.date, "predicted_kwh": p.predicted_kwh} for p in predictions]
        return Response({"trends": data})

    @extend_schema(
        summary="Prediction anomalies",
        description="Anomali sederhana: prediksi yang nilainya lebih besar dari 2x rata-rata.",
        tags=["Monitoring / Predictions"],
    )
    @action(detail=False, methods=["get"], url_path="anomalies")
    def anomalies(self, request):
        avg = self.queryset.aggregate(avg_kwh=Avg("predicted_kwh"))["avg_kwh"] or 0
        anomalies = self.queryset.filter(predicted_kwh__gt=avg * 2)
        return Response(
            {"anomalies": EnergyPredictionSerializer(anomalies, many=True).data}
        )

    @extend_schema(
        summary="Prediction recommendations",
        description="Rekomendasi sederhana berbasis total prediksi penggunaan.",
        tags=["Monitoring / Predictions"],
    )
    @action(detail=False, methods=["get"], url_path="recommendations")
    def recommendations(self, request):
        total_pred = self.queryset.aggregate(s=Sum("predicted_kwh"))["s"] or 0
        recs = []

        if total_pred > 100:
            recs.append("Reduce AC usage during peak hours")
        if total_pred > 200:
            recs.append("Switch to energy-efficient lighting")
        if not recs:
            recs.append("Current predicted usage is still within normal range")

        return Response({"recommendations": recs})


class AnalyticsViewSet(viewsets.ViewSet):
    """
    Aggregate analytics endpoints for dashboard/frontend.
    """

    def _get_date_range(self, request):
        start_raw = request.query_params.get("start_date")
        end_raw = request.query_params.get("end_date")

        end = date.fromisoformat(end_raw) if end_raw else timezone.localdate()
        start = date.fromisoformat(start_raw) if start_raw else end - timedelta(days=29)

        if start > end:
            start, end = end, start

        return start, end

    def _base_queryset(self, request):
        start, end = self._get_date_range(request)

        qs = EnergyReading.objects.select_related(
            "device",
            "device__room",
            "device__room__building",
        ).filter(timestamp__date__range=(start, end))

        building = request.query_params.get("building")
        room = request.query_params.get("room")
        floor = request.query_params.get("floor")
        device_type = request.query_params.get("device_type")
        activity = request.query_params.get("activity")

        if building:
            qs = qs.filter(device__room__building__code=building)

        if room:
            qs = qs.filter(device__room__code=room)

        if floor:
            qs = qs.filter(
                F("device__floor_label").isnull(False)
            ) | qs.filter(device__room__floor=floor)

        if device_type:
            qs = qs.filter(device__device_type=device_type)

        if activity:
            qs = qs.filter(device__activity_label=activity) | qs.filter(device__room__activity_label=activity)

        return qs, start, end

    @extend_schema(
        summary="Daily energy series",
        description="Aggregate konsumsi energi harian pada rentang tanggal tertentu.",
        parameters=[
            OpenApiParameter(name="start_date", type=str, location=OpenApiParameter.QUERY, description="Format YYYY-MM-DD"),
            OpenApiParameter(name="end_date", type=str, location=OpenApiParameter.QUERY, description="Format YYYY-MM-DD"),
            OpenApiParameter(name="building", type=str, location=OpenApiParameter.QUERY, description="Building code"),
            OpenApiParameter(name="room", type=str, location=OpenApiParameter.QUERY, description="Room code"),
            OpenApiParameter(name="floor", type=str, location=OpenApiParameter.QUERY, description="Floor label"),
            OpenApiParameter(name="device_type", type=str, location=OpenApiParameter.QUERY, description="Device type"),
            OpenApiParameter(name="activity", type=str, location=OpenApiParameter.QUERY, description="Activity label"),
        ],
        tags=["Monitoring / Analytics"],
    )
    @action(detail=False, methods=["get"], url_path="daily-series")
    def daily_series(self, request):
        qs, start, end = self._base_queryset(request)
        data = (
            qs.annotate(bucket=TruncDay("timestamp"))
            .values("bucket")
            .annotate(
                total_kwh=Coalesce(Sum("energy_kwh"), 0.0),
                avg_power=Coalesce(Avg("power_watt"), 0.0),
            )
            .order_by("bucket")
        )
        return Response(
            {
                "start_date": start,
                "end_date": end,
                "results": list(data),
            }
        )

    @extend_schema(
        summary="Weekly energy series",
        description="Aggregate konsumsi energi mingguan.",
        parameters=[
            OpenApiParameter(name="start_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="end_date", type=str, location=OpenApiParameter.QUERY),
        ],
        tags=["Monitoring / Analytics"],
    )
    @action(detail=False, methods=["get"], url_path="weekly-series")
    def weekly_series(self, request):
        qs, start, end = self._base_queryset(request)
        data = (
            qs.annotate(bucket=TruncWeek("timestamp"))
            .values("bucket")
            .annotate(total_kwh=Coalesce(Sum("energy_kwh"), 0.0))
            .order_by("bucket")
        )
        return Response(
            {
                "start_date": start,
                "end_date": end,
                "results": list(data),
            }
        )

    @extend_schema(
        summary="Monthly energy series",
        description="Aggregate konsumsi energi bulanan.",
        parameters=[
            OpenApiParameter(name="start_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="end_date", type=str, location=OpenApiParameter.QUERY),
        ],
        tags=["Monitoring / Analytics"],
    )
    @action(detail=False, methods=["get"], url_path="monthly-series")
    def monthly_series(self, request):
        qs, start, end = self._base_queryset(request)
        data = (
            qs.annotate(bucket=TruncMonth("timestamp"))
            .values("bucket")
            .annotate(total_kwh=Coalesce(Sum("energy_kwh"), 0.0))
            .order_by("bucket")
        )
        return Response(
            {
                "start_date": start,
                "end_date": end,
                "results": list(data),
            }
        )

    @extend_schema(
        summary="Consumption by room",
        description="Aggregate konsumsi energi berdasarkan ruangan.",
        parameters=[
            OpenApiParameter(name="start_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="end_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="building", type=str, location=OpenApiParameter.QUERY),
        ],
        tags=["Monitoring / Analytics"],
    )
    @action(detail=False, methods=["get"], url_path="by-room")
    def by_room(self, request):
        qs, _, _ = self._base_queryset(request)
        data = (
            qs.values("device__room__id", "device__room__code", "device__room__name")
            .annotate(
                total_kwh=Coalesce(Sum("energy_kwh"), 0.0),
                avg_power=Coalesce(Avg("power_watt"), 0.0),
                device_count=Count("device", distinct=True),
            )
            .order_by("-total_kwh", "device__room__name")
        )
        return Response(list(data))

    @extend_schema(
        summary="Consumption by floor",
        description="Aggregate konsumsi energi berdasarkan lantai.",
        parameters=[
            OpenApiParameter(name="start_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="end_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="building", type=str, location=OpenApiParameter.QUERY),
        ],
        tags=["Monitoring / Analytics"],
    )
    @action(detail=False, methods=["get"], url_path="by-floor")
    def by_floor(self, request):
        qs, _, _ = self._base_queryset(request)
        data = (
            qs.annotate(
                floor_value=Coalesce("device__floor_label", "device__room__floor")
            )
            .values("floor_value")
            .annotate(
                total_kwh=Coalesce(Sum("energy_kwh"), 0.0),
                avg_power=Coalesce(Avg("power_watt"), 0.0),
                reading_count=Count("id"),
            )
            .order_by("-total_kwh", "floor_value")
        )

        normalized = [
            {
                "floor": row["floor_value"] or "Unknown",
                "total_kwh": row["total_kwh"],
                "avg_power": row["avg_power"],
                "reading_count": row["reading_count"],
            }
            for row in data
        ]
        return Response(normalized)

    @extend_schema(
        summary="Consumption by activity",
        description="Aggregate konsumsi energi berdasarkan aktivitas/label penggunaan.",
        parameters=[
            OpenApiParameter(name="start_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="end_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="building", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="device_type", type=str, location=OpenApiParameter.QUERY),
        ],
        tags=["Monitoring / Analytics"],
    )
    @action(detail=False, methods=["get"], url_path="by-activity")
    def by_activity(self, request):
        qs, _, _ = self._base_queryset(request)
        data = (
            qs.annotate(
                activity_value=Coalesce("device__activity_label", "device__room__activity_label")
            )
            .values("activity_value", "device__device_type")
            .annotate(
                total_kwh=Coalesce(Sum("energy_kwh"), 0.0),
                avg_power=Coalesce(Avg("power_watt"), 0.0),
                reading_count=Count("id"),
            )
            .order_by("-total_kwh", "activity_value")
        )

        normalized = [
            {
                "activity": row["activity_value"] or "Unknown",
                "device_type": row["device__device_type"],
                "total_kwh": row["total_kwh"],
                "avg_power": row["avg_power"],
                "reading_count": row["reading_count"],
            }
            for row in data
        ]
        return Response(normalized)

    @extend_schema(
        summary="Consumption by device type",
        description="Aggregate konsumsi energi berdasarkan jenis device.",
        parameters=[
            OpenApiParameter(name="start_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="end_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="building", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="room", type=str, location=OpenApiParameter.QUERY),
        ],
        tags=["Monitoring / Analytics"],
    )
    @action(detail=False, methods=["get"], url_path="by-device-type")
    def by_device_type(self, request):
        qs, _, _ = self._base_queryset(request)
        data = (
            qs.values("device__device_type")
            .annotate(
                total_kwh=Coalesce(Sum("energy_kwh"), 0.0),
                avg_power=Coalesce(Avg("power_watt"), 0.0),
                reading_count=Count("id"),
            )
            .order_by("-total_kwh", "device__device_type")
        )
        return Response(list(data))

    @extend_schema(
        summary="Detailed logs with trend delta",
        description="""
Menampilkan log pembacaan detail dengan delta terhadap reading sebelumnya per device.

Output mencakup:
- identity device
- room/floor/activity
- power_watt dan energy_kwh
- delta_kwh
- delta_percent
- trend: up / down / flat
""",
        parameters=[
            OpenApiParameter(name="start_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="end_date", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="building", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="room", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="device_type", type=str, location=OpenApiParameter.QUERY),
        ],
        tags=["Monitoring / Analytics"],
    )
    @action(detail=False, methods=["get"], url_path="detailed-logs")
    def detailed_logs(self, request):
        qs, _, _ = self._base_queryset(request)

        windowed = (
            qs.annotate(
                previous_energy=Window(
                    expression=Lag("energy_kwh"),
                    partition_by=[F("device_id")],
                    order_by=F("timestamp").asc(),
                )
            )
            .select_related("device", "device__room", "device__room__building")
            .order_by("-timestamp")[:200]
        )

        data = []
        for item in windowed:
            current_energy = item.energy_kwh or 0
            prev = item.previous_energy or 0
            delta = current_energy - prev
            delta_pct = ((delta / prev) * 100) if prev else None

            room_obj = item.device.room if item.device else None

            data.append(
                {
                    "id": item.id,
                    "timestamp": item.timestamp,
                    "device_id": item.device.device_id if item.device else None,
                    "device_name": item.device.name if item.device else None,
                    "device_type": item.device.device_type if item.device else None,
                    "building": room_obj.building.code if room_obj and room_obj.building else None,
                    "room": room_obj.name if room_obj else None,
                    "room_code": room_obj.code if room_obj else None,
                    "floor": getattr(item.device, "floor_label", None) or getattr(room_obj, "floor", None),
                    "activity": getattr(item.device, "activity_label", None) or getattr(room_obj, "activity_label", None),
                    "power_watt": item.power_watt,
                    "energy_kwh": item.energy_kwh,
                    "previous_energy_kwh": item.previous_energy,
                    "delta_kwh": delta,
                    "delta_percent": delta_pct,
                    "trend": "up" if delta > 0 else ("down" if delta < 0 else "flat"),
                }
            )

        return Response(data)