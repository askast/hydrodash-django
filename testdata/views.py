import fnmatch
import json
import os
import re
from datetime import datetime, timedelta

import django_tables2 as tables2
import numpy as np
import pandas as pd
from dbfread import DBF
from django.db.models import Q
# from django.contrib.auth.decorators import login_required
# from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic.base import TemplateView, View
from django_datatables_view.base_datatable_view import BaseDatatableView
from django_tables2 import MultiTableMixin
from iapws import IAPWS95
from simpledbf import Dbf5
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from pei.utils import calculatePEI
# from profiles.views import home
from profiles.models import Profile
from pump.models import OldTestDetails

from .models import RawTestsList, ReducedPumpTestData, ReducedPumpTestDetails


class TestListView(TemplateView):
    template_name = "testdata/testlist.html"

    def get_context_data(self, **kwargs):
        path = 'Nothing'
        if (self.request.GET.get('refresh', None)):
            path = '/mnt/udrive/Lab/Test-Data/FMCommPumpEffPerfomanceTest'
            comm_eff_tests = sorted([(os.path.join(dirpath, f), (datetime.fromtimestamp(os.path.getctime(os.path.join(dirpath, f)))- timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')) for dirpath, dirnames, files in os.walk(path) for f in fnmatch.filter(files, '*(Float).DAT.dbf')], key=lambda x: x[1])
            for (testurl, testdate) in comm_eff_tests:
                if not RawTestsList.objects.filter(path=testurl).exists():
                    testname = testurl.split('/')[-1][:-16]
                    RawTestsList.objects.create(
                        path=testurl, testname=testname, testdate=testdate, testdatatype="CE")

            path = '/mnt/udrive/Lab/Test-Data/FMCommPumpStrdPerformanceTest'
            comm_perf_tests = sorted([(os.path.join(dirpath, f), (datetime.fromtimestamp(os.path.getctime(os.path.join(dirpath, f))) - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')) for dirpath, dirnames, files in os.walk(path) for f in fnmatch.filter(files, '*(Float).DAT.dbf')], key=lambda x: x[1])
            for (testurl, testdate) in comm_perf_tests:
                if not RawTestsList.objects.filter(path=testurl).exists():
                    testname = testurl.split('/')[-1][:-16]
                    RawTestsList.objects.create(
                        path=testurl, testname=testname, testdate=testdate, testdatatype="CP")

            path = '/mnt/udrive/Lab/Test-Data/S1StrdResidentialCiculatorPerfomanceTest'
            res_s1_tests = sorted([(os.path.join(dirpath, f), (datetime.fromtimestamp(os.path.getctime(os.path.join(dirpath, f))) - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')) for dirpath, dirnames, files in os.walk(path) for f in fnmatch.filter(files, '*(Float).DAT.dbf')], key=lambda x: x[1])
            for (testurl, testdate) in res_s1_tests:
                if not RawTestsList.objects.filter(path=testurl).exists():
                    testname = testurl.split('/')[-1][:-16]
                    RawTestsList.objects.create(
                        path=testurl, testname=testname, testdate=testdate, testdatatype="RS1")

            path = '/mnt/udrive/Lab/Test-Data/S2StrdResCirculatorPerfomanceTest'
            res_s2_tests = sorted([(os.path.join(dirpath, f), (datetime.fromtimestamp(os.path.getctime(os.path.join(dirpath, f))) - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')) for dirpath, dirnames, files in os.walk(path) for f in fnmatch.filter(files, '*(Float).DAT.dbf')], key=lambda x: x[1])
            print(f'{res_s2_tests:}')
            for (testurl, testdate) in res_s2_tests:
                if not RawTestsList.objects.filter(path=testurl).exists():
                    testname = testurl.split('/')[-1][:-16]
                    RawTestsList.objects.create(
                        path=testurl, testname=testname, testdate=testdate, testdatatype="RS2")

            path = '/mnt/udrive/Lab/Test-Data/Comm2StandStandard'
            comm_outside_tests = sorted([(os.path.join(dirpath, f), (datetime.fromtimestamp(os.path.getctime(os.path.join(dirpath, f))) - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S')) for dirpath, dirnames, files in os.walk(path) for f in fnmatch.filter(files, '*(Float).dbf')], key=lambda x: x[1])
            print(f'{comm_outside_tests:}')
            for (testurl, testdate) in comm_outside_tests:
                if not RawTestsList.objects.filter(path=testurl).exists():
                    testname = testurl.split('/')[-1][:-16]
                    RawTestsList.objects.create(
                        path=testurl, testname=testname, testdate=testdate, testdatatype="CO")

        context = {
            "name": self.request.user.get_full_name(),
            "servername": os.environ.get("USERNAME"),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Raw Test Data",
            "path": path,
        }
        return context


class RawTestsListData(BaseDatatableView):
    model = RawTestsList
    columns = ['id', 'testname', 'testdate', 'datareduced']
    order_columns = ['id', 'testname', 'testdate', 'datareduced']

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search = self.request.GET.get('search[value]', None)
        if search:
            for word in search.split(' '):
                qs = qs.filter(Q(id__icontains=word) | Q(
                    testname__icontains=word) | Q(testdate__icontains=word))
        # simple example:
        test_type = self.request.GET.get('testtype', None)
        if test_type == "CE":
            qs = qs.filter(testdatatype="CE")
        elif test_type == "CP":
            qs = qs.filter(testdatatype="CP")
        elif test_type == "RS1":
            qs = qs.filter(testdatatype="RS1")
        elif test_type == "RS2":
            qs = qs.filter(testdatatype="RS2")
        elif test_type == "CO":
            qs = qs.filter(testdatatype="CO")
        return qs


class TempTable(tables2.Table):
    class Meta:
        attrs = {'id': 'table1', 'class': 'table table-hover'}


class RawTestPlotView(MultiTableMixin, TemplateView):
    template_name = "testdata/rawtestplot.html"
    tables = []

    # def default(o):
    #     if isinstance(o, (datetime.date, datetime.datetime)):
    #         return o.isoformat()

    def get(self, request, *args, **kwargs):
        testid = request.GET.get('rawtestid', None)
        testpath = RawTestsList.objects.filter(
            id=testid).values("path")[0]['path']
        testname = RawTestsList.objects.filter(
            id=testid).values("testname")[0]['testname']
        testdata = [dict(f) for f in DBF(testpath, load=True).records]
        testheaders = list(testdata[0].keys())
        del_testheaders = [header for header in testheaders if "Sts" in header]
        testheaders = [header for header in testheaders if "Sts" not in header]
        removefl = request.GET.get('removefirstlast', 'false')
        if removefl == 'true':
            testdata = testdata[1:-1]  # removing first and last points

        tables = [TempTable(testdata, extra_columns=[(h, tables2.Column())
                                                     for h in testheaders])]

        context = {
            "name": request.user.get_full_name(),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Raw Test Data",
            "tables": tables,
            "testid": testid,
            "testname": testname,
            "removefl": removefl
        }
        return render(request, "testdata/rawtestplot.html", context)


epoch = datetime.utcfromtimestamp(0)


def unix_time_millis(dt):
    return (dt - epoch).total_seconds() * 1000.0


def RawTestPlotData(request):
    testid = request.GET.get('rawtestid', None)
    testpath = RawTestsList.objects.filter(
        id=testid).values("path")[0]['path']
    testname = RawTestsList.objects.filter(
        id=testid).values("testname")[0]['testname']
    testdata = [dict(f) for f in DBF(testpath, load=True).records]
    testheaders = list(testdata[0].keys())
    del_testheaders = [header for header in testheaders if "Sts" in header]
    testheaders = [header for header in testheaders if "Sts" not in header]
    # chart_time = []
    chart_flow = []
    chart_head = []
    chart_power = []
    chart_eff = []
    chart_date = []

    if request.GET.get('removefirstlast', None) == 'true':
        testdata.pop(0)
        testdata.pop(-1)  # removing first and last points

    for record in testdata:
        for header in del_testheaders:
            del record[header]
        if "FM\\FLOW" in record.keys():
            chart_flow.append(record['FM\\FLOW'])
        if "FM\\HEAD" in record.keys():
            chart_head.append(record['FM\\HEAD'])
        if "FM\\HP" in record.keys():
            chart_power.append(record['FM\\HP'])
        if "FM\\EFF" in record.keys():
            chart_eff.append(record['FM\\EFF'])
        if "Time" in record.keys():
            tempdatetime = str(record['Date'])+" "+record['Time']
            try:
                chart_date.append(unix_time_millis(datetime.strptime(
                    tempdatetime, "%Y-%m-%d %H:%M:%S.%f")))
            except:
                chart_date.append(unix_time_millis(datetime.strptime(
                    tempdatetime, "%Y-%m-%d %H:%M:%S")))

    context = {
        "testid": testid,
        "testname": testname,
        "chartflow": chart_flow,
        "charthead": chart_head,
        "chartpower": chart_power,
        "charteff": chart_eff,
        "chartdate": chart_date,
    }
    return JsonResponse(context)


class TestDataReduce(View):
    def get(self, request, *args, **kwargs):
        testnames = []
        testids = []
        testloop = request.GET.get('stand', None)
        
        if request.GET.get('rawtestids', None):
            file_extenstion = RawTestsList.objects.filter(id=request.GET.get('rawtestids', None).split(',')[0]).values("path")[0]['path'][-16:]
            if testloop == "outside":
                for testid in request.GET.get('rawtestids', None).split(','):
                    testids.append(testid)
                    testnames.append(RawTestsList.objects.filter(
                        id=testid).values("testname")[0]['testname'])

                    testpath = RawTestsList.objects.filter(
                        id=testid).values("path")[0]['path']
                    testdatadf = Dbf5(testpath).to_dataframe()
                    print(testdatadf)
                    # testdatadf = pd.pivot_table(testdatadf, index=["Millitm"], columns=['Tagname'], values=['Value'])
                    # first_id = testdatadf['Time'].iloc[0]
                    testdatadf = testdatadf.set_index(['Date', 'Time', 'Tagname'])['Value'].unstack().reset_index()
                    # print(testdatadf)
                    testheaders = list(testdatadf)
                    name = ""
                    testeng = ""
                    testloop = "Outside Loop"
                    inpipedia_in = ""
                    outpipedia_in = ""
                    description = ""
                    pump_type = ""
                    dbf_file_type = "outside"
            elif file_extenstion == " (Float).DAT.dbf":
                for testid in request.GET.get('rawtestids', None).split(','):
                    testids.append(testid)
                    testnames.append(RawTestsList.objects.filter(
                        id=testid).values("testname")[0]['testname'])

                    testpath = RawTestsList.objects.filter(
                        id=testid).values("path")[0]['path']
                    testdatadf = Dbf5(testpath).to_dataframe()
                    print(testdatadf)
                    # testdatadf = pd.pivot_table(testdatadf, index=["Millitm"], columns=['Tagname'], values=['Value'])
                    # first_id = testdatadf['Time'].iloc[0]
                    testdatadf = testdatadf.set_index(['Date', 'Time', 'Tagname'])['Value'].unstack().reset_index()
                    # print(testdatadf)
                    testheaders = list(testdatadf)
                    name = ""
                    testeng = ""
                    if testloop == "rs1":
                        testloop = "Residential Loop 1"
                    elif testloop =="rs2":
                        testloop = "Residential Loop 2"
                    elif testloop in ["insideperf", "insideeff"]:
                        pass
                    else:
                        testloop = ""
                    inpipedia_in = ""
                    outpipedia_in = ""
                    description = ""
                    pump_type = ""
                    dbf_file_type = "outside"
            else:
                for testid in request.GET.get('rawtestids', None).split(','):
                    testids.append(testid)
                    testnames.append(RawTestsList.objects.filter(
                        id=testid).values("testname")[0]['testname'])

                    testpath = RawTestsList.objects.filter(
                        id=testid).values("path")[0]['path']
                    testdata = [dict(f) for f in DBF(testpath, load=True).records]
                    testheaders = list(testdata[0].keys())
                    testheaders = [
                        header for header in testheaders if "Sts" not in header]
                    dbf_filename = testpath.split('/')[-1]
                    if OldTestDetails.objects.filter(file_name=dbf_filename).count():
                        oldtestdetailobj = OldTestDetails.objects.filter(file_name=dbf_filename).first()
                        name = getattr(oldtestdetailobj, 'name')
                        testeng = getattr(oldtestdetailobj, 'testeng')
                        testloop = getattr(oldtestdetailobj, 'teststnd')
                        inpipedia_in = getattr(oldtestdetailobj, 'inpipedia_in')
                        outpipedia_in = getattr(oldtestdetailobj, 'outpipedia_in')
                        description = getattr(oldtestdetailobj, 'description')
                        pump_type = getattr(oldtestdetailobj, 'pump_type')
                        dbf_file_type = "inside"
                    else:
                        name = ""
                        testeng = ""
                        if testloop == "rs1":
                            testloop = "Residential Loop 1"
                        elif testloop =="rs2":
                            testloop = "Residential Loop 2"
                        elif testloop in ["insideperf", "insideeff"]:
                            pass
                        else:
                            testloop = ""
                        inpipedia_in = ""
                        outpipedia_in = ""
                        description = ""
                        pump_type = ""
                        dbf_file_type = "inside"

        context = {
            "name": request.user.get_full_name(),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Raw Test Data",
            "tests": zip(testids, testnames),
            "testids": testids,
            "testheaders": testheaders,
            "oldtestname": name,
            "testeng": testeng,
            "testloop": testloop,
            "inpipe": inpipedia_in,
            "outpipe": outpipedia_in,
            "description": description,
            "pumptype": pump_type,
            "stand": dbf_file_type
        }
        return render(request, "testdata/testdatareduce.html", context)


def testDataReducePlotData(request):
    combined_testdata = []
    combined_chartdata = []

    if request.GET.get('rawtestids', None):
        flowfield = request.GET.get('flowfield', None)
        headfield = request.GET.get('headfield', None)
        powerfield = request.GET.get('powerfield', None)
        tempfield = request.GET.get('tempfield', None)
        rpmfield = request.GET.get('rpmfield', None)
        stand = request.GET.get('stand', None)
        cluster_coeff = request.GET.get('cluster', 0.1)

        for testid in request.GET.get('rawtestids', None).split(','):
            testpath = RawTestsList.objects.filter(
                id=testid).values("path")[0]['path']
            if stand == "outside":
                testdatadf = Dbf5(testpath).to_dataframe()
                first_id = testdatadf['Time'].iloc[0]
                testdatadf = testdatadf.set_index(['Date', 'Time', 'Tagname'])['Value'].unstack().reset_index()
                testdatadf = testdatadf[testdatadf.Time != first_id]
                [combined_chartdata.append([f[flowfield], f[headfield]]) for index, f in testdatadf.iterrows()]
                if rpmfield != "":
                    [combined_testdata.append({"flow": f[flowfield], "head":f[headfield], "power":f[powerfield], "temp":f[tempfield], "rpm":f[rpmfield]}) for index, f in testdatadf.iterrows()]
                else:
                    [combined_testdata.append({"flow": f[flowfield], "head":f[headfield], "power":f[powerfield], "temp":f[tempfield], "rpm":None}) for index, f in testdatadf.iterrows()]
                print(combined_chartdata)
                print(combined_testdata)
            else:
                [combined_chartdata.append([dict(f)[flowfield], dict(
                    f)[headfield]]) for index, f in enumerate(DBF(testpath, load=True).records) if index != 0]
                # print(f"\n\n\n\nrpmfield:{rpmfield}\n\n\n")
                if rpmfield != "":
                    [combined_testdata.append({"flow": dict(f)[flowfield], "head":dict(f)[headfield], "power":dict(
                        f)[powerfield], "temp":dict(f)[tempfield], "rpm":dict(f)[rpmfield]}) for index, f in enumerate(DBF(testpath, load=True).records) if index != 0]
                else:
                    [combined_testdata.append({"flow": dict(f)[flowfield], "head":dict(f)[headfield], "power":dict(
                        f)[powerfield], "temp":dict(f)[tempfield], "rpm":None}) for index, f in enumerate(DBF(testpath, load=True).records) if index != 0]
                # print(combined_chartdata)
                # print(combined_testdata)
            
        combined_chartdata_array = np.array(combined_chartdata)
        X = StandardScaler().fit_transform(combined_chartdata_array)
        # #############################################################################
        # Compute DBSCAN
        print(f"Cluster coeff:{cluster_coeff}")
        db = DBSCAN(eps=float(cluster_coeff), min_samples=1).fit(X)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        labels = db.labels_
        combined_chartdata_list = np.hstack(
            (combined_chartdata_array, np.array([labels]).T)).tolist()
        for index, label in enumerate(labels):
            combined_testdata[index]["label"] = int(label)
        # Number of clusters in labels, ignoring noise if present.
        # n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        # n_noise_ = list(labels).count(-1)

    context = {
        "chartdata": combined_chartdata_list,
        "testdata": combined_testdata
    }
    return JsonResponse(context)


def testNameValidate(request):
    testname = request.POST.get('testname', None)
    if ReducedPumpTestDetails.objects.filter(testname=testname).exists():
        return HttpResponse("false")
    else:
        return HttpResponse("true")


def convertTemptoK(value, units):
    if units == "Celsius":
        return value+273.15
    elif units == "Fahrenheit":
        return (((value-32)*5/9)+273.15)
    elif units == "Rankine":
        return value*5/9
    return value

def convertKtoTemp(value, units):
    if units == "Celsius":
        return value-273.15
    elif units == "Fahrenheit":
        return (((value-273.15)*9/5)+32)
    elif units == "Rankine":
        return value*9/5
    return value


def reduceTestData(request):
    testname = request.POST.get('testname', None)
    testeng = request.POST.get('testeng', None)
    testloop = request.POST.get('testloop', None)
    dispipedia = request.POST.get('dispipedia', None)
    inpipedia = request.POST.get('inpipedia', None)
    pumptype = request.POST.get('pumptype', None)
    description = request.POST.get('description', None)
    testdata = json.loads(request.POST.get('testdata', None))
    flowunits = request.POST.get('flowunits', None)
    headunits = request.POST.get('headunits', None)
    powerunits = request.POST.get('powerunits', None)
    tempunits = request.POST.get('tempunits', None)
    diameter = float(re.findall(r'[-+]?\d*\.\d+|\d+', request.POST.get('diameter', None))[0])
    fulltrim = request.POST.get('fulltrim', None)
    bearingframe = request.POST.get('bearingframe', None)
    source = list(map(int, request.POST.get('source', None).split(",")))
    stand = request.POST.get('stand', None)

    testpath = RawTestsList.objects.filter(
        id=source[0]).values("path")[0]['path']
    record = dict(DBF(testpath, load=True).records[1])
    tempdatetime = str(record['Date'])+" "+record['Time']
    print(f"stand:{stand}")
    # if stand in ["outside", "rs2"] :
    #     testdate = datetime.strptime(
    #         tempdatetime, "%Y-%m-%d %H:%M:%S") + timedelta(hours=4)
    # else:
    #     testdate = datetime.strptime(
    #         tempdatetime, "%Y-%m-%d %H:%M:%S.%f") + timedelta(hours=4)
    try:
        testdate = datetime.strptime(
            tempdatetime, "%Y-%m-%d %H:%M:%S") + timedelta(hours=4)
    except:
        testdate = datetime.strptime(
            tempdatetime, "%Y-%m-%d %H:%M:%S.%f") + timedelta(hours=4)

    if fulltrim == 'on':
        fulltrim = True
    else:
        fulltrim = False
    
    testDetailsObj = ReducedPumpTestDetails(testname=testname, testeng=testeng, testloop=testloop, discharge_pipe_dia=dispipedia, inlet_pipe_dia=inpipedia, description=description,
                                            testdate=testdate, pumptype=pumptype, imp_dia=diameter, fulltrim=fulltrim, bearingframe=bearingframe)
    testDetailsObj.save()

    rawTestObj = RawTestsList.objects.filter(pk__in=source)
    rawTestObj.update(datareduced=True)

    testDetailsObj.data_sources.add(*rawTestObj)
    testDetailsObj.save()

    flowunitconversionfactor = 1
    headunitconversionfactor = 1
    powerunitconversionfactor = 1
    # Database to store values in SI Units with clear water at specific gravity 1.0
    # Flow - m3/hr
    # Head - m
    # Power - KW
    # Temperature - Kelvin

    if flowunits == "Gallons per minute":
        flowunitconversionfactor = 0.227125
    elif flowunits == "Liters per second":
        flowunitconversionfactor = 3.6
    if headunits == "Feet":
        headunitconversionfactor = 0.3048
    elif flowunits == "Millimeters":
        headunitconversionfactor = 0.001
    if powerunits == "Horsepower":
        powerunitconversionfactor = .7457
    elif powerunits == "Watts":
        powerunitconversionfactor = 0.001

    unique_labels = {datapoint['label'] for datapoint in testdata}
    for label in unique_labels:
        testdata_subset = [
            datapoint for datapoint in testdata if datapoint['label'] == label]
        count = len(testdata_subset)
        sumOfFlows = 0
        sumOfHeads = 0
        sumOfPowers = 0
        sumOfRPMs = 0
        sumOfTemps = 0
        for datapoint in testdata_subset:
            sumOfFlows += datapoint['flow']
            sumOfHeads += datapoint['head']
            sumOfPowers += abs(datapoint['power'])
            sumOfTemps += datapoint['temp']
            if datapoint['rpm']:
                sumOfRPMs += datapoint['rpm']

        avgTemp = convertTemptoK(sumOfTemps/count, tempunits)
        water_props = IAPWS95(T=avgTemp, x=0)
        ref_water_props = IAPWS95(T=277.15, x=0)
        specific_gravity = water_props.rho/ref_water_props.rho

        avgFlow = sumOfFlows/count*flowunitconversionfactor
        if -.05<=avgFlow<=0:
            avgFlow = 0
        avgHead = sumOfHeads/count*headunitconversionfactor
        avgPower = sumOfPowers/count*powerunitconversionfactor/specific_gravity
        avgRPM = sumOfRPMs/count
        testDataObj = ReducedPumpTestData(
            testid=testDetailsObj, flow=avgFlow, head=avgHead, power=avgPower, temp=avgTemp, rpm=avgRPM)
        testDataObj.save()

    context = {
        "result": "success",
        "testname": testname
    }
    return JsonResponse(context)


class ReducedTestListView(TemplateView):
    template_name = "testdata/reducedtestlist.html"

    def get_context_data(self, **kwargs):

        context = {
            "name": self.request.user.get_full_name(),
            "servername": os.environ.get("USERNAME"),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Reduced Test Data",
        }
        return context


class ReducedTestsListData(BaseDatatableView):
    model = ReducedPumpTestDetails
    columns = ['id', 'testdate', 'testname', 'testeng', 'testloop', 'discharge_pipe_dia', 'inlet_pipe_dia', 'bep_flow', 'bep_head', 'bep_efficiency', 'peicl', 'peivl', 'pumptype', 'imp_dia', 'fulltrim', 'bearingframe', 'data_sources', 'description']

    def prepare_results(self, qs):
        data = []

        for item in qs:
            sources = []
            for source in item.data_sources.all():
                sources.append(str(source.id))
            sources = ', '.join(sources)

            data.append([item.id, item.testdate, item.testname, item.testeng, item.testloop, item.discharge_pipe_dia, item.inlet_pipe_dia,
                         item.bep_flow, item.bep_head, item.bep_efficiency, item.peicl, item.peivl, item.pumptype, item.imp_dia, item.fulltrim, item.bearingframe, sources , item.description])
        return data

    def filter_queryset(self, qs):
        # use request parameters to filter queryset
        search = self.request.GET.get('search[value]', None)
        if search:
            for word in search.split(' '):
                qs = qs.filter(Q(id__icontains=word) | Q(testname__icontains=word) | Q(testdate__icontains=word) | Q(testeng__icontains=word) | Q(
                    discharge_pipe_dia__icontains=word) | Q(inlet_pipe_dia__icontains=word) | Q(description__icontains=word) | Q(pumptype__icontains=word))
        return qs


class ReducedTestTable(tables2.Table):
    class Meta:
        model = ReducedPumpTestData
        attrs = {'id': 'table1', 'class': 'table table-hover'}


class ReducedTestPlotView(TemplateView):
    template_name = "testdata/reducedtestplot.html"

    def get_context_data(self, **kwargs):
        testid = self.request.GET.get('testid', None)
        testdetail = ReducedPumpTestDetails.objects.filter(id=testid)
        testname = testdetail.values("testname")[0]['testname']
        impdia = testdetail.values("imp_dia")[0]['imp_dia']

        context = {
            "name": self.request.user.get_full_name(),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Reduced Test Data",
            "testid": testid,
            "testname": testname,
            "impdia": impdia
        }
        return context


def reducedTestPlotData(request):
    user = request.user
    flow_units = Profile.objects.filter(user = user).values('flow_units')[0]['flow_units']
    head_units = Profile.objects.filter(user = user).values('head_units')[0]['head_units']
    power_units = Profile.objects.filter(user = user).values('power_units')[0]['power_units']
    
    flowunitconversionfactor = 1
    headunitconversionfactor = 1
    powerunitconversionfactor = 1
    if flow_units == "Gallons per minute":
        flowunitconversionfactor = 4.402862
    elif flow_units == "Liters per second":
        flowunitconversionfactor = 0.277778
    if head_units == "Feet":
        headunitconversionfactor = 3.28084
    elif head_units == "Millimeters":
        headunitconversionfactor = 1000
    if power_units == "Horsepower":
        powerunitconversionfactor = 1.34102
    elif power_units == "Watts":
        powerunitconversionfactor = 1000

    testid = request.GET.get('testid', None)
    testdetail = ReducedPumpTestDetails.objects.filter(id=testid)
    testname = testdetail.values("testname")[0]['testname']
    pumptype = testdetail.values("pumptype")[0]['pumptype']
    impdia = testdetail.values("imp_dia")[0]['imp_dia']
    full_trim = testdetail.values("fulltrim")[0]['fulltrim']
    bearingframe = testdetail.values("bearingframe")[0]['bearingframe']

    testdata = list(ReducedPumpTestData.objects.filter(
        testid=testdetail[0]).values('flow', 'head', 'power', 'rpm'))
    inlet_diameter = testdetail.values('inlet_pipe_dia')[0]['inlet_pipe_dia']*25.4
    discharge_diameter = testdetail.values('discharge_pipe_dia')[0]['discharge_pipe_dia']*25.4

    chart_flow = []
    chart_head = []
    chart_power = []
    chart_eff = []
    chart_rpm = []
    table_data = []

    for record in testdata:
        chart_flow.append(float(record['flow']))
        chart_head.append(float(record['head']))
        chart_power.append(float(record['power']))
        if(record['rpm']):
            chart_rpm.append(float(record['rpm']))
        else:
            chart_rpm.append(None)
    
    
    nominal_rpm = int(request.GET.get('nominalrpm', 0))
    if nominal_rpm == 0 and chart_rpm[0]:
        if 1120 <= chart_rpm[0] <= 1260:
            nominal_rpm = 1160
        elif 1400 <= chart_rpm[0] <= 1575:
            nominal_rpm = 1450
        elif 1650 <= chart_rpm[0] <= 1890:
            nominal_rpm = 1760
        elif 2800 <= chart_rpm[0] <= 3150:
            nominal_rpm = 2900
        elif 3400 <= chart_rpm[0] <= 3780:
            nominal_rpm = 3500
        else:
            nominal_rpm = 0

    speed_correction = request.GET.get('speedcorrection', None)
    if nominal_rpm != 0 and speed_correction != 'false':
        for index, value in enumerate(chart_flow):
            chart_flow[index] = chart_flow[index]*nominal_rpm/chart_rpm[index]
            chart_head[index] = chart_head[index]*((nominal_rpm/chart_rpm[index])**2)
            chart_power[index] = chart_power[index]*((nominal_rpm/chart_rpm[index])**3)
            chart_rpm[index] = nominal_rpm
    
    diameter_correction = request.GET.get('diacorrection', None)
    if diameter_correction != 'false':
        for index, flow in enumerate(chart_flow):
            chart_head[index] += 6380*(((flow**2)/discharge_diameter**4)-((flow**2)/inlet_diameter**4))

    for flow, head, power in zip(chart_flow, chart_head, chart_power):
        if power > 0:
            eff = flow*head/(367*power)*100
        else:
            eff = 0
        chart_eff.append(eff)

    for index, value in enumerate(chart_flow):
        chart_flow[index] = chart_flow[index]*flowunitconversionfactor
        chart_head[index] = chart_head[index]*headunitconversionfactor
        chart_power[index] = chart_power[index]*powerunitconversionfactor
        table_data.append([chart_flow[index], chart_head[index], chart_eff[index], chart_power[index], chart_rpm[index]])

    head_poly_degree = int(request.GET.get('headdeg', 6))
    power_poly_degree = int(request.GET.get('powdeg', 6))
    eff_poly_degree = int(request.GET.get('effdeg', 6))
    head_poly = np.poly1d(np.polyfit(np.array(chart_flow), np.array(chart_head), head_poly_degree))
    power_poly = np.poly1d(np.polyfit(np.array(chart_flow), np.array(chart_power), power_poly_degree))
    chart_flow_fit = np.linspace(min(chart_flow), max(chart_flow), 2000)
    chart_head_fit = list(head_poly(chart_flow_fit))
    chart_power_fit = list(power_poly(chart_flow_fit))
    if chart_power_fit[0] > 0:
        chart_eff_fit = list(chart_flow_fit/flowunitconversionfactor*np.array(chart_head_fit)/headunitconversionfactor/(np.array(chart_power_fit)/powerunitconversionfactor*367)*100)
    else:
        chart_eff_fit = list(np.zeros(len(chart_power_fit)))
    chart_flow_fit = list(chart_flow_fit)
    bep_eff = max(chart_eff_fit)
    bep_index = chart_eff_fit.index(bep_eff)
    bep_flow = chart_flow_fit[bep_index]
    bep_head = chart_head_fit[bep_index]
    bep_power = chart_power_fit[bep_index]
    max_power = max(chart_power_fit)
    flow_75 = chart_flow_fit[int(bep_index*0.75)]/flowunitconversionfactor
    head_75 = chart_head_fit[int(bep_index*0.75)]/headunitconversionfactor
    power_75 = chart_power_fit[int(bep_index*0.75)]/powerunitconversionfactor
    flow_110 = chart_flow_fit[min([int(bep_index*1.1), len(chart_power_fit)-1])]/flowunitconversionfactor
    head_110 = chart_head_fit[min([int(bep_index*1.1), len(chart_power_fit)-1])]/headunitconversionfactor
    power_110 = chart_power_fit[min([int(bep_index*1.1), len(chart_power_fit)-1])]/powerunitconversionfactor
    power_120 = chart_power_fit[min([int(bep_index*1.2), len(chart_power_fit)-1])]/powerunitconversionfactor
    pei_bep_flow = chart_flow_fit[bep_index]/flowunitconversionfactor
    pei_bep_head = chart_head_fit[bep_index]/headunitconversionfactor
    pei_bep_power = chart_power_fit[bep_index]/powerunitconversionfactor
    # print(f'Full_trim: {full_trim}')
    if full_trim:
        pei_result = calculatePEI(bep_flow=pei_bep_flow, bep_head=pei_bep_head, bep_power=pei_bep_power, flow_75=flow_75, head_75=head_75, power_75=power_75, flow_110=flow_110, head_110=head_110, power_110=power_110, power_120=power_120, tempRPM=nominal_rpm, pump_type=pumptype, test_type='BP')
        if pei_result["status"] == "success":
            PEIcl = pei_result["PEIcl"]
            PEIvl = pei_result["PEIvl"]
        else:
            print(f"PEI reason: {pei_result['reason']}")
            PEIcl = 0.0
            PEIvl = 0.0
    else:
        PEIcl = 0.0
        PEIvl = 0.0

    context = {
        "testid": testid,
        "testname": testname,
        "impdia": impdia,
        "bearingframe": bearingframe,
        "chartflow": chart_flow,
        "charthead": chart_head,
        "chartpower": chart_power,
        "charteff": chart_eff,
        "chartflowfit": chart_flow_fit,
        "chartheadfit": chart_head_fit,
        "chartpowerfit": chart_power_fit,
        "chartefffit": chart_eff_fit,
        "chartrpm": chart_rpm,
        "tabledata": table_data,
        "flowunits": flow_units,
        "headunits": head_units,
        "powerunits": power_units,
        "bepeff": bep_eff,
        "bepflow": bep_flow,
        "bephead": bep_head,
        "maxpow": max_power,
        "nomrpm": nominal_rpm,
        "peicl": PEIcl,
        "peivl": PEIvl,
        "fulltrim": full_trim
    }
    return JsonResponse(context)

def addSummary(request):
    testid = request.GET.get('testid', None)
    bep_flow = request.GET.get('bepflow', None)
    bep_head = request.GET.get('bephead', None)
    flow_units = request.GET.get('flowunits', None)
    head_units = request.GET.get('headunits', None)
    bep_eff = request.GET.get('bepeff', None)
    trimdia = request.GET.get('trimdia', None)
    testdetail = ReducedPumpTestDetails.objects.filter(id=testid)
    testname = testdetail.values("testname")[0]['testname']
    full_trim = testdetail.values("fulltrim")[0]['fulltrim']
    imp_dia = testdetail.values("imp_dia")[0]['imp_dia']
    print(f'imp_dia: {imp_dia}')
    if full_trim == True:
        peicl = request.GET.get('peicl', None)
        peivl = request.GET.get('peivl', None)

    testObj = ReducedPumpTestDetails.objects.filter(id=testid)
    if imp_dia == None and trimdia != 'None':
        testObj.update(imp_dia=trimdia)

    if full_trim == True:
        testObj.update(bep_flow=bep_flow, bep_head=bep_head, bep_efficiency=bep_eff, peicl=peicl, peivl=peivl)
        return JsonResponse({'status': 'success', 'bepflow': round(float(bep_flow), 2), 'bephead':round(float(bep_head), 2), 'bepeff':round(float(bep_eff), 2), 'testname': testname, 'peicl':round(float(peicl),2), 'peivl':round(float(peivl), 2)})
    else:
        testObj.update(bep_flow=bep_flow, bep_head=bep_head, bep_efficiency=bep_eff)
        return JsonResponse({'status': 'success', 'bepflow': round(float(bep_flow), 2), 'bephead':round(float(bep_head), 2), 'bepeff':round(float(bep_eff), 2), 'testname': testname, 'peicl':0, 'peivl':0})

class DirectDataInputView(View):
    template_name = "testdata/directdatainput.html"

    def get(self, request, *args, **kwargs):
        # pumps = list(
        #     Pump.objects.order_by("series", "pump_model", "design_iteration", "-speed")
        #     .distinct("series", "pump_model", "design_iteration")
        #     .values_list("series", "pump_model", "design_iteration", "speed", "id")
        # )
        # pumpdata = [
        #     (pump_id, f"{series}{pumpmodel}{design} {speed}RPM")
        #     for (series, pumpmodel, design, speed, pump_id) in pumps
        # ]

        context = {
            "name": self.request.user.get_full_name(),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Direct Data Input",
            # "pumps": pumpdata,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        testname = request.POST.get('testname', None)
        testeng = request.POST.get('testeng', None)
        testloop = request.POST.get('testloop', None)
        dispipedia = request.POST.get('dispipedia', None)
        inpipedia = request.POST.get('inpipedia', None)
        pumptype = request.POST.get('pumptype', None)
        description = request.POST.get('description', None)
        testdatatext = request.POST.get('testdata', None)
        flowunits = "Gallons per minute"
        headunits = "Feet"
        powerunits = "Horsepower"
        tempunits = "Fahrenheit"
        diameter = float(re.findall(r'[-+]?\d*\.\d+|\d+', request.POST.get('diameter', None))[0])
        fulltrim = request.POST.get('fulltrim', None)
        bearingframe = request.POST.get('bearingframe', None)
        stand = request.POST.get('stand', None)

        if fulltrim == 'on':
            fulltrim = True
        else:
            fulltrim = False
        
        testDetailsObj = ReducedPumpTestDetails(testname=testname, testeng=testeng, testloop=testloop, discharge_pipe_dia=dispipedia, inlet_pipe_dia=inpipedia, description=description,
                                                testdate=datetime.now(), pumptype=pumptype, imp_dia=diameter, fulltrim=fulltrim, bearingframe=bearingframe)
        testDetailsObj.save()


        flowunitconversionfactor = 1
        headunitconversionfactor = 1
        powerunitconversionfactor = 1
        # Database to store values in SI Units with clear water at specific gravity 1.0
        # Flow - m3/hr
        # Head - m
        # Power - KW
        # Temperature - Kelvin

        if flowunits == "Gallons per minute":
            flowunitconversionfactor = 0.227125
        elif flowunits == "Liters per second":
            flowunitconversionfactor = 3.6
        if headunits == "Feet":
            headunitconversionfactor = 0.3048
        elif flowunits == "Millimeters":
            headunitconversionfactor = 0.001
        if powerunits == "Horsepower":
            powerunitconversionfactor = .7457
        elif powerunits == "Watts":
            powerunitconversionfactor = 0.001



        values = []
        for line in testdatatext.split('\n'):
            # print(f'line: {line}')
            if not re.search("[a-zA-Z]", line):
                if(line.strip()):
                    split_line = re.split(' |,|\t', line)
                    print(f"split_line: {split_line}")
                    avgTemp = convertTemptoK(float(split_line[4]), tempunits)

                    water_props = IAPWS95(T=avgTemp, x=0)
                    ref_water_props = IAPWS95(T=277.15, x=0)
                    specific_gravity = water_props.rho/ref_water_props.rho

                    avgFlow = float(split_line[0])*flowunitconversionfactor
                    if -.05<=avgFlow<=0:
                        avgFlow = 0
                    avgHead = float(split_line[1])*headunitconversionfactor
                    avgPower = float(split_line[2])*powerunitconversionfactor/specific_gravity
                    avgRPM = float(split_line[3])
                    testDataObj = ReducedPumpTestData(
                        testid=testDetailsObj, flow=avgFlow, head=avgHead, power=avgPower, temp=avgTemp, rpm=avgRPM)
                    testDataObj.save()

        context = {
            "result": "success",
            "testname": testname
        }
        return JsonResponse(context)



class KeysightDaqView(View):
    template_name = "testdata/keysightdaqtest.html"

    def get(self, request, *args, **kwargs):

        context = {
            "name": self.request.user.get_full_name(),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Keysight DAQ Test",
        }
        return render(request, self.template_name, context)