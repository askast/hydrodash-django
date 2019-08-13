from django.contrib import admin

# Register your models here.
from .models import Pump, PumpTrim, NPSHData

admin.site.register(Pump)
admin.site.register(PumpTrim)
admin.site.register(NPSHData)
