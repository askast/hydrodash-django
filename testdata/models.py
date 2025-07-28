from django.db import models


class RawTestsList(models.Model):
    testdatatype_choices = (
        ("CE", "Commercial Efficiency"),
        ("CP", "Commercial Standard Performance"),
        ("RS1", "Residential Stand 1"),
        ("RS2", "Residential Stand 2"),
        ("CO", "Commercial Outside Stand"),
    )

    headunits_choices = (("ft", "Feet of water"), ("m", "meters of water"))
    powerunits_choices = (("W", "Watts"), ("KW", "Kilo Watts"), ("HP", "Horsepower"))
    flowunits_choices = (
        ("gpm", "Gallons per minute"),
        ("m3ph", "Cubic meter per hour"),
        ("lpm", "liters per minute"),
    )
    tempunits_choices = (("ftlbf", "Feet Pound Force"), ("Nm", "Newton meter"))
    headfield = models.CharField(max_length=20, blank=True, null=True)
    flowfield = models.CharField(max_length=20, blank=True, null=True)
    powerfield = models.CharField(max_length=20, blank=True, null=True)
    torquefield = models.CharField(max_length=20, blank=True, null=True)
    headunits = models.CharField(
        max_length=10, blank=True, choices=headunits_choices, null=True
    )
    flowunits = models.CharField(
        max_length=20, blank=True, choices=flowunits_choices, null=True
    )
    powerunits = models.CharField(
        max_length=20, blank=True, choices=powerunits_choices, null=True
    )
    tempunits = models.CharField(
        max_length=20, blank=True, choices=tempunits_choices, null=True
    )
    rpmfield = models.CharField(max_length=20, blank=True, null=True)
    path = models.CharField(verbose_name="URL", max_length=400, blank=True, null=True)
    testname = models.CharField(verbose_name="Test Record Name", max_length=100)
    testdate = models.DateTimeField(verbose_name="Date")
    datareduced = models.BooleanField(default=False, verbose_name="Data Reduced")
    fileupload = models.BooleanField(verbose_name="File Upload", blank=True, null=True)
    hidden = models.BooleanField(blank=True, null=True)
    testdatatype = models.CharField(
        verbose_name="Test Stand",
        choices=testdatatype_choices,
        max_length=200,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.testname


class ReducedPumpTestDetails(models.Model):
    pumptype_choices = (
        ("FI", "FI"),
        ("CI", "CI"),
        ("KV", "KV"),
        ("KS", "KS"),
        ("TA", "TA"),
        ("TS", "TS"),
        ("TC", "TC"),
        ("SKV", "SKV"),
        ("SKS", "SKS"),
        ("SFI", "SFI"),
        ("SCI", "SCI"),
        ("ESCC", "End suction close-coupled"),
        ("ESFM", "End suction frame mounted/own bearings"),
        ("IL", "In-Line"),
        ("RSV", "Radially split, multi-stage, vertical, in-line casing diffuser"),
        ("ST", "Submersible turbine"),
        ("Circ", "Residential Circulator"),
        ("1600", "1600"),
        ("1900", "1900"),
        ("HS", "HS"),
        ("GT", "GT"),
    )
    testloop_choices = (
        ("C1", "Commercial Front Loop"),
        ("C2", "Commercial Back Loop"),
        ("R1", "Residential Loop 1"),
        ("R2", "Residential Loop 2"),
        ("CO", "Commercial Outside Loop"),
    )
    bearingframe_choices = (
        ("H", "H Frame"),
        ("J", "J Frame"),
        ("L", "L Frame"),
        ("N", "N Frame"),
        ("N/A", "None"),
    )
    testname = models.CharField(max_length=200)
    testeng = models.CharField(max_length=100, blank=True, null=True)
    testloop = models.CharField(max_length=100, blank=True, null=True)
    discharge_pipe_dia = models.FloatField()
    inlet_pipe_dia = models.FloatField()
    description = models.CharField(max_length=2000, blank=True, null=True)
    testdate = models.DateTimeField()
    bep_flow = models.FloatField(blank=True, null=True)
    bep_head = models.FloatField(blank=True, null=True)
    bep_efficiency = models.FloatField(blank=True, null=True)
    peicl = models.FloatField(blank=True, null=True)
    peivl = models.FloatField(blank=True, null=True)
    pumptype = models.CharField(max_length=100, choices=pumptype_choices)
    imp_dia = models.FloatField(blank=True, null=True)
    fulltrim = models.BooleanField(default=False)
    bearingframe = models.CharField(
        max_length=10, blank=True, null=True, choices=bearingframe_choices
    )
    data_sources = models.ManyToManyField(
        "testdata.RawTestsList", related_name="used_in", blank=True
    )

    def __str__(self):
        return f"{self.id} {self.testname}"


class ReducedPumpTestData(models.Model):
    testid = models.ForeignKey(ReducedPumpTestDetails, on_delete=models.CASCADE)
    flow = models.FloatField()
    head = models.FloatField()
    power = models.FloatField()
    temp = models.FloatField()
    rpm = models.FloatField(null=True)

    def __str__(self):
        return f"{self.testid.id} {self.testid.testname} flow:{self.flow*4.402862} head:{self.head*3.28084}"
