from django.db import models
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

