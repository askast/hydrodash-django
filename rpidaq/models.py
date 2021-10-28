from django.db import models

# Create your models here.

class RpiDaqTestDetails(models.Model):
    testname = models.CharField(verbose_name="Test Record Name", max_length=100)
    testdate = models.DateTimeField(verbose_name="Date")
    description = models.CharField(max_length=2000, blank=True, null=True)

    def __str__(self):
        return f"{self.id} {self.testname}"

class RpiDaqData(models.Model):
    testid = models.ForeignKey(RpiDaqTestDetails, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    channel_1 = models.FloatField(blank=True, null=True)
    channel_2 = models.FloatField(blank=True, null=True)
    channel_3 = models.FloatField(blank=True, null=True)
    channel_4 = models.FloatField(blank=True, null=True)
    channel_5 = models.FloatField(blank=True, null=True)
    channel_6 = models.FloatField(blank=True, null=True)
    channel_7 = models.FloatField(blank=True, null=True)
    channel_8 = models.FloatField(blank=True, null=True)
    channel_9 = models.FloatField(blank=True, null=True)
    channel_10 = models.FloatField(blank=True, null=True)
    channel_11 = models.FloatField(blank=True, null=True)
    channel_12 = models.FloatField(blank=True, null=True)
    channel_13 = models.FloatField(blank=True, null=True)
    channel_14 = models.FloatField(blank=True, null=True)
    channel_15 = models.FloatField(blank=True, null=True)
    channel_16 = models.FloatField(blank=True, null=True)
    channel_17 = models.FloatField(blank=True, null=True)
    channel_18 = models.FloatField(blank=True, null=True)
    channel_19 = models.FloatField(blank=True, null=True)
    channel_21 = models.FloatField(blank=True, null=True)
    channel_22 = models.FloatField(blank=True, null=True)
    channel_23 = models.FloatField(blank=True, null=True)
    channel_24 = models.FloatField(blank=True, null=True)
    channel_25 = models.FloatField(blank=True, null=True)
    channel_26 = models.FloatField(blank=True, null=True)
    channel_27 = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.testid.id} {self.testid.testname} id:{self.id}"
