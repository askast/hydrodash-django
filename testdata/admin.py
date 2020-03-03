from django.contrib import admin

# Register your models here.

from .models import RawTestsList, ReducedPumpTestDetails, ReducedPumpTestData

class ReducedPumpTestDataAdmin(admin.ModelAdmin):
    search_fields = ["testid__id", "testid__testname"]




admin.site.register(RawTestsList)
admin.site.register(ReducedPumpTestDetails)
admin.site.register(ReducedPumpTestData, ReducedPumpTestDataAdmin)
