from django.contrib.postgres.fields import ArrayField
from django.db import models
from testdata.models import ReducedPumpTestDetails


class MarketingCurveDetail(models.Model):
    pumptype_choices = (
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
    curvename = models.CharField(max_length=200)
    bep_flow = models.FloatField(blank=True, null=True)
    bep_head = models.FloatField(blank=True, null=True)
    bep_efficiency = models.FloatField(blank=True, null=True)
    peicl = models.FloatField(blank=True, null=True)
    peivl = models.FloatField(blank=True, null=True)
    ercl = models.FloatField(blank=True, null=True)
    ervl = models.FloatField(blank=True, null=True)
    pumptype = models.CharField(max_length=100, choices=pumptype_choices)
    imp_dia = models.FloatField(blank=True, null=True)
    fulltrim = models.BooleanField(default=False)
    headcoeffs = ArrayField(models.FloatField(), blank=True)
    effcoeffs = ArrayField(models.FloatField(), blank=True)
    powercoeffs = ArrayField(models.FloatField(), blank=True)
    rpm = models.FloatField()
    data_source = models.ForeignKey(ReducedPumpTestDetails, on_delete=models.CASCADE)

    def __str__(self):
        return self.curvename


class MarketingCurveData(models.Model):
    curveid = models.ForeignKey(MarketingCurveDetail, on_delete=models.CASCADE)
    flow = models.FloatField()
    head = models.FloatField()
    power = models.FloatField()
    efficiency = models.FloatField()

    def __str__(self):
        return f"{self.curveid.id} {self.curveid.curvename} flow:{self.flow*4.402862} head:{self.head*3.28084}"
