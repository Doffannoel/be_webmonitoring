from django.db import models

# Create your models here.
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Building(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=30, unique=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
class Room(TimeStampedModel):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=30)
    
    class Meta:
        unique_together = [('building', 'code')]
        
    def __str__(self):
        return f"{self.building.code}/{self.code} - {self.name}"

# Device masih meraba raba (paling nanti disesuaikan lagi ama kresna)
class Device(TimeStampedModel):
    DEVICE_TYPES = [
        ("meter", "Energy Meter"),
        ("ac", "Air Conditioner"),
        ("light", "Lighting"),
        ("other", "Other"),   
    ]
    
    device_id = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default="meter")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices')
    
    # metadata
    brand = models.CharField(max_length=100, blank=True, null=True, default="")
    model = models.CharField(max_length=100, blank=True, null=True, default="")
    capacity_watt = models.FloatField(null=True,blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.device_id} - {self.name}"
    
class ThresholdRule(TimeStampedModel):
    """
    Rules untuk bikin Alert otomatis (scalable).
    Bisa per device, atau per room (kalau device kosong).
    """
    SEVERITY = [("info", "Info"), ("warning", "Warning"), ("critical", "Critical")]

    name = models.CharField(max_length=120)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name="threshold_rules")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True, related_name="threshold_rules")

    # threshold sederhana: power_watt > x
    power_watt_gt = models.FloatField(null=True, blank=True)

    severity = models.CharField(max_length=10, choices=SEVERITY, default="warning")
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        scope = self.device.device_id if self.device else (self.room.code if self.room else "global")
        return f"{self.name} ({scope})"
    
    