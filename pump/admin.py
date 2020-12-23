from django.contrib import admin

# Register your models here.
from .models import Pump, PumpTrim, NPSHData, SubmittalCurve, OldTestDetails


class PumpAdmin(admin.ModelAdmin):
    search_fields = ["series", "pump_model", "speed"]


class PumpTrimAdmin(admin.ModelAdmin):
    search_fields = ["pump__series", "pump__pump_model", "pump__speed"]
    autocomplete_fields = ["pump"]


class NPSHDataAdmin(admin.ModelAdmin):
    search_fields = ["pump__series", "pump__pump_model", "pump__speed"]
    autocomplete_fields = ["pump"]


class SubmittalCurveAdmin(admin.ModelAdmin):
    search_fields = ["pump__series", "pump__pump_model", "pump__speed"]
    autocomplete_fields = ["pump"]


admin.site.register(Pump, PumpAdmin)
admin.site.register(PumpTrim, PumpTrimAdmin)
admin.site.register(NPSHData, NPSHDataAdmin)
admin.site.register(SubmittalCurve, SubmittalCurveAdmin)
admin.site.register(OldTestDetails)
