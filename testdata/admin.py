from django.contrib import admin

# Register your models here.

from .models import RawTestsList, ReducedPumpTestDetails, ReducedPumpTestData

admin.site.register(RawTestsList)
admin.site.register(ReducedPumpTestDetails)
admin.site.register(ReducedPumpTestData)
