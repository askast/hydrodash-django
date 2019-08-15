from django.db import models
from django.contrib.postgres.fields import ArrayField
from testdata.models import ReducedPumpTestDetails
from marketingdata.models import MarketingCurveDetail


class Pump(models.Model):
    series_choices = (
        ("FI", "FI"),
        ("CI", "CI"),
        ("KV", "KV"),
        ("KS", "KS"),
        ("TA", "TA"),
        ("SKV", "SKV"),
        ("SKS", "SKS"),
        ("SFI", "SFI"),
        ("SCI", "SCI"),
        ("Circ", "Residential Circulator"),
    )
    speed_choices = (
        (1160, "1160 RPM"),
        (1450, "1450 RPM"),
        (1760, "1760 RPM"),
        (2900, "2900 RPM"),
        (3500, "3500 RPM"),
    )
    series = models.CharField(max_length=100, choices=series_choices)
    pump_model = models.CharField(max_length=100)
    design_iteration = models.CharField(max_length=10, blank=True, null=True)
    speed = models.IntegerField(choices=speed_choices)
    curve_number = models.CharField(max_length=100, default="00000")
    curve_rev = models.CharField(max_length=200, default="00000")

    def __str__(self):
        return f"{self.series}{self.pump_model}{self.design_iteration} {self.speed}RPM"


class PumpTrim(models.Model):
    pump = models.ForeignKey(Pump, on_delete=models.CASCADE)
    trim = models.FloatField()
    engineering_data = models.ForeignKey(
        ReducedPumpTestDetails, on_delete=models.SET_NULL, blank=True, null=True
    )
    marketing_data = models.ForeignKey(
        MarketingCurveDetail, on_delete=models.SET_NULL, blank=True, null=True
    )

    def __str__(self):
        return f'{self.pump.series}{self.pump.pump_model}{self.pump.design_iteration} {self.trim}" {self.pump.speed}RPM'


class NPSHData(models.Model):
    pump = models.ForeignKey(Pump, on_delete=models.CASCADE)
    flow = models.FloatField()
    npsh = models.FloatField()

    def __str__(self):
        return f"{self.pump.series}{self.pump.pump_model}{self.pump.design_iteration} {self.pump.speed}RPM"


class SubmittalCurve(models.Model):
    pump = models.ForeignKey(Pump, on_delete=models.CASCADE)
    max_motor_hp = models.FloatField()
    min_motor_hp = models.FloatField()
    eff_levels = ArrayField(models.FloatField())
    power_manual_location_flows = ArrayField(models.FloatField())
    power_manual_location_heads = ArrayField(models.FloatField())
    x_axis_limits = ArrayField(models.FloatField())
    y_axis_limits = ArrayField(models.FloatField())
    created_on = models.DateTimeField(blank=True)
    current_approved = models.BooleanField(default=False)
    curve_svg = models.FileField(upload_to="submittal_curves/", null=True, blank=True)
    curve_pdf = models.FileField(upload_to="submittal_curves/", null=True, blank=True)
    curve_jpg = models.FileField(upload_to="submittal_curves/", null=True, blank=True)
    # max_motor_hp = 3
    # min_motor_hp = 1
    # eff_levels = [60, 65, 70, 73, 75, 77]
    # power_manual_location_flows = [150, 175, 185, 200]
    # power_manual_location_heads = [14, 18, 25, 40]
    # x_axis_limits = [0, 225]
    # y_axis_limits = [0, 65]
    # l_per_sec_offset = 0.08

    def __str__(self):
        return f"{self.id}: {self.pump.series}{self.pump.pump_model}{self.pump.design_iteration} {self.pump.speed}RPM"
