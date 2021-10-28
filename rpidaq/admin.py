from django.contrib import admin

# Register your models here.
from .models import RpiDaqTestDetails, RpiDaqData

class RpiDaqDataAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at', )

admin.site.register(RpiDaqTestDetails)
admin.site.register(RpiDaqData, RpiDaqDataAdmin)
