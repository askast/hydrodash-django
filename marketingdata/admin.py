from django.contrib import admin

# Register your models here.
from .models import MarketingCurveDetail, MarketingCurveData

admin.site.register(MarketingCurveDetail)
admin.site.register(MarketingCurveData)
