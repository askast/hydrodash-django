from django.contrib import admin

# Register your models here.

from .models import RawTestsList, ReducedPumpTestDetails, ReducedPumpTestData

class ReducedPumpTestDataAdmin(admin.ModelAdmin):
    search_fields = ["testid__id", "testid__testname"]
    list_display = ['testid', 'flow', 'head', 'power', 'temp', 'rpm',]
    list_editable = ['flow', 'head', 'power', 'temp', 'rpm',]

# class RawTestsListAdmin(admin.ModelAdmin):
#     list_display = ['headfield', 'flowfield', 'powerfield', 'torquefield', 'headunits', 'flowunits', 'powerunits', 'tempunits', 'rpmfield', 'path', 'testname', 'testdate', 'datareduced', 'fileupload', 'hidden', 'testdatatype', ]
#     list_editable = ['headfield', 'flowfield', 'powerfield', 'torquefield', 'headunits', 'flowunits', 'powerunits', 'tempunits', 'rpmfield', 'path', 'testname', 'testdate', 'datareduced', 'fileupload', 'hidden', 'testdatatype', ] 

    
# admin.site.register(RawTestsList, RawTestsListAdmin)
admin.site.register(RawTestsList)
admin.site.register(ReducedPumpTestDetails)
admin.site.register(ReducedPumpTestData, ReducedPumpTestDataAdmin)
