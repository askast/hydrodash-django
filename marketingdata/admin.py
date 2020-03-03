from django.contrib import admin

# Register your models here.
from .models import MarketingCurveDetail, MarketingCurveData


class MarketingCurveDataAdmin(admin.ModelAdmin):
    search_fields = ["curveid__curvename"]


admin.site.register(MarketingCurveDetail)
admin.site.register(MarketingCurveData, MarketingCurveDataAdmin)
