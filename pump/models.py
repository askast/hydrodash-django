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
        ("1600", "1600"),
        ("1900", "1900"),
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
    x_axis_limit = models.FloatField()
    y_axis_limit = models.FloatField()
    created_on = models.DateTimeField(blank=True)
    current_approved = models.BooleanField(default=False)
    # smoothed = models.BooleanField(default=False)
    curve_ids = ArrayField(models.IntegerField())
    npsh_flows = ArrayField(models.FloatField())
    npsh_npshs = ArrayField(models.FloatField())
    curve_svg = models.FileField(upload_to="submittal_curves/", null=True, blank=True)
    curve_pdf = models.FileField(upload_to="submittal_curves/", null=True, blank=True)

    def __str__(self):
        return f"{self.id}: {self.pump.series}{self.pump.pump_model}{self.pump.design_iteration} {self.pump.speed}RPM"


class OldTestDetails(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    testeng = models.CharField(max_length=100, null=True, blank=True)
    teststnd = models.CharField(max_length=100, null=True, blank=True)
    inpipedia_in = models.FloatField(null=True, blank=True)
    outpipedia_in = models.FloatField(null=True, blank=True)
    description = models.CharField(max_length=1000, null=True, blank=True)
    testconfigs_id = models.IntegerField(null=True, blank=True)
    pump_type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.CharField(max_length=100, null=True, blank=True)
    file_name = models.CharField(max_length=200, null=True, blank=True)
    averaged = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name
