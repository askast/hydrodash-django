import json
import numpy as np
import numpy.polynomial.polynomial as P
from scipy.interpolate import UnivariateSpline
import re

from django.http import JsonResponse
from django.views.generic.base import TemplateView
from django.shortcuts import render
from django.views import View
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.db.models import Q

from .models import MarketingCurveDetail, MarketingCurveData
from pump.models import Pump, PumpTrim, NPSHData
from testdata.models import ReducedPumpTestDetails
from pei.utils import calculatePEI
from profiles.models import Profile


def fudgeData(request):
    """

    :param request: 

    """
    curvedata = json.loads(request.POST.get("curvedata", None))
    flattendroop = request.POST.get("flattendroop", None)
    bepshift = request.POST.get("bepshift", None)
    print(f"bepshift:{bepshift}")
    targeteff = request.POST.get("targeteff", None)
    flowunits = request.POST.get("flowunits", None)
    headunits = request.POST.get("headunits", None)
    powerunits = request.POST.get("powerunits", None)
    bearingframe = request.POST.get("bearingframe", None)
    bearinglossremoval = request.POST.get("bearinglossremoval", None)
    rpm = int(request.POST.get("rpm", None))

    flowunitconversionfactor = 1
    headunitconversionfactor = 1
    powerunitconversionfactor = 1
    if flowunits == "Gallons per minute":
        flowunitconversionfactor = 0.227125
    elif flowunits == "Liters per second":
        flowunitconversionfactor = 3.6
    if headunits == "Feet":
        headunitconversionfactor = 0.3048
    elif flowunits == "Millimeters":
        headunitconversionfactor = 0.001
    if powerunits == "Horsepower":
        powerunitconversionfactor = 0.7457
    elif powerunits == "Watts":
        powerunitconversionfactor = 0.001

    flow = []
    head = []
    eff = []
    power = []
    headcoeffs = []
    effcoeffs = []

    for flowpoint, headpoint, powerpoint in zip(
        curvedata["flow"], curvedata["head"], curvedata["power"]
    ):
        flow.append(flowpoint * flowunitconversionfactor)
        head.append(headpoint * headunitconversionfactor)
        power.append(powerpoint * powerunitconversionfactor)

    max_index = len(flow) - 1

    flow = np.array(flow)
    head = np.array(head)
    power = np.array(power)

    if flattendroop:
        print("Checking Flattening Droop")
        maxhead = -20
        index = 0
        for index, headpoint in enumerate(np.flip(head)):
            if headpoint > maxhead:
                maxhead = headpoint
            else:
                break

        maxheadindex = max_index - index

        for index in range(0, maxheadindex):
            print("Flattening Droop")
            head[index] = maxhead

        head_poly = np.poly1d(np.flip(P.polyfit(flow, head, 6)))
        head = head_poly(flow)
        headcoeffs = list(
            np.flip(P.polyfit(
                flow / flowunitconversionfactor, head / headunitconversionfactor, 5
            ))
        )
    else:
        head_poly = np.poly1d(np.flip(P.polyfit(flow, head, 6)))
        head = head_poly(flow)
        headcoeffs = list(
            np.flip(P.polyfit(
                flow / flowunitconversionfactor, head / headunitconversionfactor, 5
            ))
        )


    eff = head * flow / (power * 367)
    # print(f"eff:{eff}")
    bep_eff = np.amax(eff)

    if targeteff:
        print("multiplying Efficiency")
        targeteff = float(targeteff)
        effmultiplier = targeteff / (bep_eff * 100)
        power = power / effmultiplier
    

    if bearinglossremoval:
        print("Removing Bearing Loss")
        if bearingframe == "H":
            if rpm == 1160:
                bearingloss = 0.011931
            elif rpm == 1450:
                bearingloss = 0.017897
            elif rpm == 1760:
                bearingloss = 0.025354
            elif rpm == 2900:
                bearingloss = 0.063012
            elif rpm == 3500:
                bearingloss = 0.089484
            else:
                bearingloss = 0
        elif bearingframe == "J":
            if rpm == 1160:
                bearingloss = 0.023862
            elif rpm == 1450:
                bearingloss = 0.035794
            elif rpm == 1760:
                bearingloss = 0.050708
            elif rpm == 2900:
                bearingloss = 0.126023
            elif rpm == 3500:
                bearingloss = 0.178968
            else:
                bearingloss = 0
        elif bearingframe == "L":
            if rpm == 1160:
                bearingloss = 0.035794
            elif rpm == 1450:
                bearingloss = 0.05369
            elif rpm == 1760:
                bearingloss = 0.076061
            elif rpm == 2900:
                bearingloss = 0.189035
            elif rpm == 3500:
                bearingloss = 0.268452
            else:
                bearingloss = 0
        elif bearingframe == "N":
            if rpm == 1160:
                bearingloss = 0.047725
            elif rpm == 1450:
                bearingloss = 0.071587
            elif rpm == 1760:
                bearingloss = 0.101415
            elif rpm == 2900:
                bearingloss = 0.252047
            elif rpm == 3500:
                bearingloss = 0.357936
            else:
                bearingloss = 0
        else:
            bearingloss = 0

        power = power - bearingloss

    eff = head * flow / (power * 367)

    bep_eff = np.amax(eff)
    bep_index = list(eff).index(bep_eff)
    bep_flow = flow[bep_index]
    

    # CHECK THIS!!!!!!!!!!!!!!!
    if bepshift != "0":
        bepshift = float(bepshift)
        print("Shifting BEP")
        shiftflow = []
        for index, flowpoint in enumerate(flow):
            if index <= bep_index:
                shiftflow.append(flowpoint - bep_flow * bepshift/100 * index / bep_index)
            else:
                shiftflow.append(
                    flowpoint
                    - bep_flow * bepshift/100 * ((index - max_index) / (bep_index - max_index))
                )

        shift_eff_poly = UnivariateSpline(np.array(shiftflow), eff, s=0.000001)
        eff = shift_eff_poly(flow)

    powerpts = head * flow / (eff * 367)
    power_poly = np.poly1d(
        np.flip(P.polyfit(flow[int(0.05 * max_index) :], powerpts[int(0.05 * max_index) :], 6))
    )
    power = power_poly(flow)
    eff = head * flow / (power * 367)

    effcoeffs = list(np.flip(P.polyfit(flow / flowunitconversionfactor, eff, 6)))
    powercoeffs = list(
        np.flip(P.polyfit(
            flow / flowunitconversionfactor, power / powerunitconversionfactor, 5
        ))
    )
    power = list(power / powerunitconversionfactor)
    flow = list(flow / flowunitconversionfactor)
    head = list(head / headunitconversionfactor)
    eff = list(eff * 100)

    context = {
        "flow": flow,
        "head": head,
        "power": power,
        "efficiency": eff,
        "headcoeffs": headcoeffs,
        "effcoeffs": effcoeffs,
        "powercoeffs": powercoeffs,
        "flowunits": flowunits,
        "headunits": headunits,
        "powerunits": powerunits,
    }

    return JsonResponse(context)


def getPumpModels(request):
    """

    :param request: 

    """
    series = request.GET.get("series", None)
    pumpmodels = list(
        Pump.objects.filter(series=series)
        .order_by("pump_model")
        .values_list("pump_model", flat=True)
        .distinct()
    )
    context = {"pumpmodels": pumpmodels}
    return JsonResponse(context)


def getDesignIts(request):
    """

    :param request: 

    """
    series = request.GET.get("series", None)
    pumpmodel = request.GET.get("pumpmodel", None)
    designits = list(
        Pump.objects.filter(series=series, pump_model=pumpmodel)
        .order_by()
        .values_list("design_iteration", flat=True)
        .distinct()
    )
    designits.sort()
    context = {"designs": designits}
    return JsonResponse(context)


def getRPMs(request):
    """

    :param request: 

    """
    series = request.GET.get("series", None)
    pumpmodel = request.GET.get("pumpmodel", None)
    designit = request.GET.get("design", None)
    rpms = list(
        Pump.objects.filter(
            series=series, pump_model=pumpmodel, design_iteration=designit
        )
        .order_by()
        .values_list("speed", flat=True)
        .distinct()
    )
    rpms.sort()
    context = {"rpms": rpms}
    return JsonResponse(context)


def getTrims(request):
    """

    :param request: 

    """
    series = request.GET.get("series", None)
    pumpmodel = request.GET.get("pumpmodel", None)
    designit = request.GET.get("design", None)
    rpm = request.GET.get("rpm", None)
    trims = list(
        PumpTrim.objects.filter(
            pump__series=series,
            pump__pump_model=pumpmodel,
            pump__design_iteration=designit,
            pump__speed=rpm,
        )
        .values_list("trim", flat=True)
        .distinct()
    )
    trims.sort()
    context = {"trims": trims}
    return JsonResponse(context)


def addMarketingData(request):
    """

    :param request: 

    """
    curvename = request.POST.get("curvename", None)
    series = request.POST.get("series", None)
    pumpmodel = request.POST.get("pumpmodel", None)
    designit = request.POST.get("design", None)
    rpm = float(request.POST.get("rpm", None))
    trim = request.POST.get("trim", None)
    curvedata = json.loads(request.POST.get("curvedata", None))
    curveheadcoefficients = json.loads(request.POST.get("curveheadcoefficients", None))
    curveeffcoefficients = json.loads(request.POST.get("curveeffcoefficients", None))
    curvepowercoefficients = json.loads(
        request.POST.get("curvepowercoefficients", None)
    )
    fulltrim = request.POST.get("fulltrim", None)
    flowunits = request.POST.get("flowunits", None)
    headunits = request.POST.get("headunits", None)
    powerunits = request.POST.get("powerunits", None)
    testid = request.POST.get("testid", None)

    flowunitconversionfactor = 1
    headunitconversionfactor = 1
    powerunitconversionfactor = 1
    if flowunits == "Gallons per minute":
        flowunitconversionfactor = 0.227125
    elif flowunits == "Liters per second":
        flowunitconversionfactor = 3.6
    if headunits == "Feet":
        headunitconversionfactor = 0.3048
    elif flowunits == "Millimeters":
        headunitconversionfactor = 0.001
    if powerunits == "Horsepower":
        powerunitconversionfactor = 0.7457
    elif powerunits == "Watts":
        powerunitconversionfactor = 0.001

    eff = np.array(curvedata["eff"]) / 100
    flow = np.array(curvedata["flow"]) * flowunitconversionfactor
    head = np.array(curvedata["head"]) * headunitconversionfactor
    power = np.array(curvedata["power"]) * powerunitconversionfactor

    bep_eff = np.amax(eff)
    bep_index = list(eff).index(bep_eff)
    bep_flow = flow[bep_index]
    bep_head = head[bep_index]
    bep_power = power[bep_index]
    max_power = max(power)
    flow_75 = flow[int(bep_index * 0.75)]
    head_75 = head[int(bep_index * 0.75)]
    power_75 = power[int(bep_index * 0.75)]
    flow_110 = flow[int(bep_index * 1.1)]
    head_110 = head[int(bep_index * 1.1)]
    power_110 = power[int(bep_index * 1.1)]
    if 1.2*bep_index < len(eff):
        power_120 = power[int(bep_index * 1.2)]
    else:
        power_120 = power[-1]
    pei_bep_flow = flow[bep_index]
    pei_bep_head = head[bep_index]
    pei_bep_power = power[bep_index]

    if fulltrim == "true":
        fulltrim = True
        pei_result = calculatePEI(
            bep_flow=pei_bep_flow,
            bep_head=pei_bep_head,
            bep_power=pei_bep_power,
            flow_75=flow_75,
            head_75=head_75,
            power_75=power_75,
            flow_110=flow_110,
            head_110=head_110,
            power_110=power_110,
            power_120=power_120,
            tempRPM=rpm,
            pump_type=series,
            test_type="BP",
        )
        if pei_result["status"] == "success":
            PEIcl = pei_result["PEIcl"]
            PEIvl = pei_result["PEIvl"]
        else:
            PEIcl = 0.0
            PEIvl = 0.0
    else:
        fulltrim = False
        PEIcl = 0.0
        PEIvl = 0.0

    # extract 30 points from head flow and power.
    # get testdata object
    # create marketing details table
    # get marketing data object
    # update and add testdata and marketing data as foregn keys to pump object
    # add marketing data to table using details as foregn key.
    flow_subset = flow[:: int(len(flow) / 29)]
    head_subset = head[:: int(len(head) / 29)]
    power_subset = power[:: int(len(power) / 29)]
    eff_subset = flow_subset * head_subset / (power_subset * 367)

    testdataObj = ReducedPumpTestDetails.objects.filter(id=testid)[0]

    curveDetailObj = MarketingCurveDetail(
        curvename=curvename,
        bep_flow=bep_flow,
        bep_head=bep_head,
        bep_efficiency=bep_eff,
        peicl=PEIcl,
        peivl=PEIvl,
        fulltrim=fulltrim,
        rpm=rpm,
        pumptype=series,
        imp_dia=trim,
        data_source=testdataObj,
        headcoeffs=curveheadcoefficients,
        effcoeffs=curveeffcoefficients,
        powercoeffs=curvepowercoefficients,
    )
    curveDetailObj.save()

    if series and pumpmodel and designit and rpm and trim:
        pumptrim = PumpTrim.objects.filter(
            pump__series=series,
            pump__pump_model=pumpmodel,
            pump__design_iteration=designit,
            pump__speed=rpm,
            trim=trim,
        )
        pumptrim.update(engineering_data=testdataObj, marketing_data=curveDetailObj)

    for flowpoint, headpoint, powerpoint, effpoint in zip(
        flow_subset, head_subset, power_subset, eff_subset
    ):
        curveDataObj = MarketingCurveData(
            curveid=curveDetailObj,
            flow=flowpoint,
            head=headpoint,
            power=powerpoint,
            efficiency=effpoint,
        )
        curveDataObj.save()

    context = {"status": "success"}
    return JsonResponse(context)


class MarketingCurveListView(TemplateView):
    """ """

    template_name = "marketingdata/marketingcurvelist.html"

    def get_context_data(self, **kwargs):
        """

        :param **kwargs: 

        """

        # populatePumps()
        context = {
            "name": self.request.user.get_full_name(),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Performance Curves",
        }
        return context


class MarketingCurveListData(BaseDatatableView):
    """ """

    model = MarketingCurveDetail
    columns = [
        "id",
        "curvename",
        "bep_flow",
        "bep_head",
        "bep_efficiency",
        "peicl",
        "peivl",
        "pumptype",
        "imp_dia",
        "fulltrim",
        "rpm",
        "data_source",
        "headcoeffs",
        "effcoeffs",
    ]

    def prepare_results(self, qs):
        """

        :param qs: 

        """
        user = self.request.user
        flow_units = Profile.objects.filter(user=user).values("flow_units")[0][
            "flow_units"
        ]
        head_units = Profile.objects.filter(user=user).values("head_units")[0][
            "head_units"
        ]
        power_units = Profile.objects.filter(user=user).values("power_units")[0][
            "power_units"
        ]

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

        data = []
        for item in qs:
            data.append(
                [
                    item.id,
                    item.curvename,
                    item.bep_flow * flowunitconversionfactor,
                    item.bep_head * headunitconversionfactor,
                    item.bep_efficiency * 100,
                    item.peicl,
                    item.peivl,
                    item.pumptype,
                    item.imp_dia,
                    item.fulltrim,
                    item.rpm,
                    str(item.data_source.id),
                    item.headcoeffs,
                    item.effcoeffs,
                ]
            )
        return data

    def filter_queryset(self, qs):
        """

        :param qs: Queryset containing all the results

        """
        # use request parameters to filter queryset
        search = self.request.GET.get("search[value]", None)
        if search:
            for word in search.split(" "):
                qs = qs.filter(
                    Q(id__icontains=word)
                    | Q(curvename__icontains=word)
                    | Q(pumptype__icontains=word)
                )
        return qs


# class MarketingCurveTable(tables2.Table):
#     class Meta:
#         model = MarketingCurveData
#         attrs = {'id': 'table1', 'class': 'table table-hover'}


class MarketingCurveView(TemplateView):
    """ """

    template_name = "marketingdata/marketingcurveplot.html"

    def get_context_data(self, **kwargs):
        """

        :param **kwargs: 

        """
        curveid = self.request.GET.get("curveid", None)
        curvedetail = MarketingCurveDetail.objects.filter(id=curveid)
        curvename = curvedetail.values("curvename")[0]["curvename"]

        context = {
            "name": self.request.user.get_full_name(),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Performance Curves",
            "curveid": curveid,
            "curvename": curvename,
        }
        return context


def marketingCurvePlotData(request):
    """

    :param request: 

    """
    user = request.user
    flow_units = Profile.objects.filter(user=user).values("flow_units")[0]["flow_units"]
    head_units = Profile.objects.filter(user=user).values("head_units")[0]["head_units"]
    power_units = Profile.objects.filter(user=user).values("power_units")[0][
        "power_units"
    ]

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

    curveid = request.GET.get("curveid", None)
    curvedetail = MarketingCurveDetail.objects.filter(id=curveid)
    curvename = curvedetail.values("curvename")[0]["curvename"]
    peicl = curvedetail.values("peicl")[0]["peicl"]
    peivl = curvedetail.values("peivl")[0]["peivl"]
    bepflow = curvedetail.values("bep_flow")[0]["bep_flow"] * flowunitconversionfactor
    bephead = curvedetail.values("bep_head")[0]["bep_head"] * headunitconversionfactor
    bepeff = curvedetail.values("bep_efficiency")[0]["bep_efficiency"]

    curvedata = list(
        MarketingCurveData.objects.filter(curveid=curvedetail[0]).values(
            "flow", "head", "power", "efficiency"
        ).order_by("flow")
    )

    flow = []
    head = []
    power = []
    eff = []
    table_data = []

    for record in curvedata:
        flow.append(float(record["flow"]) * flowunitconversionfactor)
        head.append(float(record["head"]) * headunitconversionfactor)
        power.append(float(record["power"]) * powerunitconversionfactor)
        eff.append(float(record["efficiency"]))
        table_data.append([flow[-1], head[-1], eff[-1], power[-1]])

    context = {
        "curveid": curveid,
        "curvename": curvename,
        "peicl": peicl,
        "peivl": peivl,
        "bepflow": bepflow,
        "bephead": bephead,
        "bepeff": bepeff,
        "maxpower": max(power),
        "flow": flow,
        "head": head,
        "power": power,
        "eff": eff,
        "tabledata": table_data,
        "flowunits": flow_units,
        "headunits": head_units,
        "powerunits": power_units,
    }
    return JsonResponse(context)


class NPSHDataInput(View):
    template_name = "marketingdata/marketingnpshdatainput.html"

    def get(self, request, *args, **kwargs):
        pumps = list(
            Pump.objects.order_by("series", "pump_model", "design_iteration", "-speed")
            .distinct("series", "pump_model", "design_iteration")
            .values_list("series", "pump_model", "design_iteration", "speed", "id")
        )
        pumpdata = [
            (pump_id, f"{series}{pumpmodel}{design} {speed}RPM")
            for (series, pumpmodel, design, speed, pump_id) in pumps
        ]

        context = {
            "name": self.request.user.get_full_name(),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "NPSH Data",
            "pumps": pumpdata,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        pumpid = request.POST.get("pump", None)
        npshText = request.POST.get("npshdata", None)
        # add NPSH data to all pumps
        pump = Pump.objects.get(id=pumpid)
        ref_speed = getattr(pump, "speed")
        ref_series = getattr(pump, "series")
        ref_model = getattr(pump, "pump_model")
        ref_design = getattr(pump, "design_iteration")
        pumpqs = Pump.objects.filter(
            series=ref_series, pump_model=ref_model, design_iteration=ref_design
        )

        values = []
        for line in npshText.split('\n'):
            # print(f'line: {line}')
            if not re.search("[a-zA-Z]", line):
                if(line.strip()):
                    if "," in line:
                        values.append(
                            (float(line.split(",")[0]), float(line.split(",")[1]))
                        )
                    elif "\t" in line:
                        values.append(
                            (float(line.split("\t")[0]), float(line.split("\t")[1]))
                        )
                    else:
                        values.append(
                            (float(line.split(" ")[0]), float(line.split()[1]))
                        )

        for pumpobj in pumpqs:
            NPSHData.objects.filter(pump=pumpobj).delete()
            for flow, npsh in values:
                npshobj = NPSHData(
                    pump=pumpobj,
                    flow=flow / 4.402862 * pumpobj.speed / ref_speed,
                    npsh=npsh / 3.28084 * pow(pumpobj.speed / ref_speed, 2),
                )
                npshobj.save()

        context = {"status": "success"}
        return JsonResponse(context)


class MarketingMapView(TemplateView):
    """ """

    template_name = "marketingdata/marketingmap.html"

    def get_context_data(self, **kwargs):
        """

        :param **kwargs: 

        """

        context = {
            "name": self.request.user.get_full_name(),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Family of Curves",
        }
        return context


def marketingMapData(request):
    """

    :param request: 

    """
    user = request.user
    flow_units = Profile.objects.filter(user=user).values("flow_units")[0]["flow_units"]
    head_units = Profile.objects.filter(user=user).values("head_units")[0]["head_units"]
    power_units = Profile.objects.filter(user=user).values("power_units")[0][
        "power_units"
    ]

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

    FI_pumps = [
        [1206, "D"],
        [1506, "D"],
        [2506, "D"],
        [1207, "D"],
        [1507, "D"],
        [2007, "D"],
        [2507, "D"],
        [3007, "D"],
        [4007, "D"],
        [5007, "D"],
        [1209, "B"],
        [1509, "D"],
        [2009, "D"],
        [2509, "D"],
        [3009, "D"],
        [4009, "D"],
        [5009, "D"],
        [6009, "D"],
        [2510, "C"],
        [1511, "B"],
        [2511, "D"],
        [3011, "D"],
        [4011, "B"],
        [5011, "D"],
        [6011, "D"],
        [2513, "D"],
        [3013, "D"],
        [4013, "D"],
        [5013, "D"],
        [6013, "D"],
        [8013, "D"],
    ]
    CI_pumps = [
        [1206, "D"],
        [1506, "D"],
        [2506, "D"],
        [1207, "D"],
        [1507, "D"],
        [2007, "D"],
        [2507, "D"],
        [3007, "D"],
        [4007, "D"],
        [5007, "D"],
        [1209, "B"],
        [1509, "D"],
        [2009, "D"],
        [2509, "D"],
        [3009, "D"],
        [4009, "D"],
        [5009, "D"],
        [6009, "D"],
        [2510, "C"],
        [1511, "B"],
        [2511, "D"],
        [3011, "D"],
        [4011, "B"],
        [5011, "D"],
        [6011, "D"],
        [2513, "D"],
        [3013, "D"],
        [4013, "D"],
    ]
    KV_pumps = [
        [1506, "D"],
        [2006, "D"],
        [3006, "D"],
        [1507, "D"],
        [2007, "D"],
        [3007, "D"],
        [4007, "D"],
        [5007, "D"],
        [6007, "D"],
        [1509, "C"],
        [2009, "D"],
        [3009, "D"],
        [4009, "D"],
        [6009, "D"],
        [2011, "C"],
        [3011, "D"],
        [4011, "D"],
        [6011, "D"],
        [8011, "D"],
        [3013, "D"],
        [4013, "D"],
        [6013, "D"],
        [8013, "D"],
    ]
    KS_pumps = [
        [1506, "D"],
        [2006, "D"],
        [3006, "D"],
        [1507, "D"],
        [2007, "D"],
        [3007, "D"],
        [4007, "D"],
        [5007, "D"],
        [6007, "D"],
        [1509, "C"],
        [2009, "D"],
        [3009, "D"],
        [4009, "D"],
        [6009, "D"],
        [2011, "C"],
        [3011, "D"],
        [4011, "D"],
        [6011, "D"],
        [8011, "D"],
        [3013, "D"],
        [4013, "D"],
        [6013, "D"],
        [8013, "D"],
        [1013, "A"],
        [1213, "B"],
        [8016, "A"],
        [1016, "A"],
        [1415, "B"],
        [1217, "A"],
    ]
    HS_pumps = [
        ["060509", "A"],
        ["060511", "A"],
        ["060512", "A"],
        ["060515", "A"],
    ]

    return_pump_data = {}

    for model, design in FI_pumps:
        pump_speeds = list(
            Pump.objects.filter(series="FI", pump_model=model, design_iteration=design)
            .values_list("speed", flat=True)
        )
        # print(f"model: FI{model}{design}")
        for speed in pump_speeds:
            pump_trims = list(PumpTrim.objects.filter(
                pump__series="FI",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
            ).values_list("trim", flat=True))
            # print(f" speed: {speed} trims:{pump_trims}")
            max_trim = max(pump_trims)
            min_trim = min(pump_trims)
            max_trim_id, max_trim_head_coeffs, max_trim_bep_flow, max_trim_bep_head = PumpTrim.objects.filter(
                pump__series="FI",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=max_trim
            ).values_list(
                "marketing_data__id",
                "marketing_data__headcoeffs",
                "marketing_data__bep_flow",
                "marketing_data__bep_head",
            )[
                0
            ]
            min_trim_head_coeffs, = PumpTrim.objects.filter(
                pump__series="FI",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=min_trim
            ).values_list(
                "marketing_data__headcoeffs",
            )[0]

            max_trim_bep_flow = max_trim_bep_flow*flowunitconversionfactor
            max_trim_bep_head = max_trim_bep_head*headunitconversionfactor
            # print(f"max_trim_id: {max_trim_id}")
            max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.6*max_trim_bep_flow)
            # print(f"max_trim_head_coeffs: {max_trim_head_coeffs}")
            # print(f"min_trim_head_coeffs: {min_trim_head_coeffs}")
            max_poly = np.poly1d(max_trim_head_coeffs)
            min_poly = np.poly1d(min_trim_head_coeffs)
            max_trim_flow_pts = np.linspace(5, max_trim_max_flow, 30)
            max_trim_head_pts = max_poly(max_trim_flow_pts)
            cutoff_curve = np.poly1d(np.flip(P.polyfit([0, max_trim_max_flow], [0, max_poly(max_trim_max_flow)], 2)))
            # print(f"min_poly: \n{min_poly}\ncutoff_curve: \n{cutoff_curve}")
            # find roots
            x_0 = (min_poly - cutoff_curve).roots
            # print(f"roots:{x_0}")
            # print(f"max_flow:{max_trim_max_flow}")
            # select roots in specific range only
            min_trim_max_flow = min(np.real(x_0[(x_0 > 0) & (x_0 < max_trim_max_flow*1.1) & np.isreal(x_0)]))
            # print(f"root:{min_trim_max_flow}")
            
            min_trim_flow_pts = np.linspace(min_trim_max_flow, 5, 30)
            min_trim_head_pts = min_poly(min_trim_flow_pts)

            plot_flows = np.append(max_trim_flow_pts, min_trim_flow_pts)
            plot_flows_metric = plot_flows*0.0630902
            plot_heads = np.append(max_trim_head_pts, min_trim_head_pts)
            plot_heads_metric = plot_heads*0.3048
            plot_heads_kpa = plot_heads*2.98898
            plot_data = np.column_stack((plot_flows, plot_heads))
            plot_data_metric = np.column_stack((plot_flows_metric, plot_heads_metric))
            plot_data_kpa = np.column_stack((plot_flows, plot_heads_kpa))

            temp_model = "a"+str(model)
            if "FI" not in return_pump_data:
                return_pump_data["FI"] = {}
            if temp_model not in return_pump_data["FI"]:
                return_pump_data["FI"][temp_model] = {}
            if design not in return_pump_data["FI"][temp_model]:
                return_pump_data["FI"][temp_model][design] = {}
            if speed not in return_pump_data["FI"][temp_model][design]:
                return_pump_data["FI"][temp_model][design][speed] = {}
            
            # return_pump_data["FI"][temp_model][design][speed]["max_coeffs"] = max_trim_head_coeffs
            # return_pump_data["FI"][temp_model][design][speed]["min_coeffs"] = min_trim_head_coeffs
            # return_pump_data["FI"][temp_model][design][speed]["max_flow"] = max_trim_max_flow

            if speed in [1160, 1760, 3500]:
                return_pump_data["FI"][temp_model][design][speed]["plot_data"] = plot_data.tolist()
            else:
                return_pump_data["FI"][temp_model][design][speed]["plot_data_metric"] = plot_data_metric.tolist()

            return_pump_data["FI"][temp_model][design][speed]["plot_data_kpa"] = plot_data_kpa.tolist()
            return_pump_data["FI"][temp_model][design][speed]["label_location"] = [max_trim_bep_flow, (max_poly(max_trim_max_flow)+max_trim_bep_head*1.5)/2.5]

    for model, design in CI_pumps:
        pump_speeds = list(
            Pump.objects.filter(series="CI", pump_model=model, design_iteration=design)
            .values_list("speed", flat=True)
        )
        # print(f"model: CI{model}{design}")
        for speed in pump_speeds:
            pump_trims = list(PumpTrim.objects.filter(
                pump__series="CI",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
            ).values_list("trim", flat=True))
            # print(f" speed: {speed} trims:{pump_trims}")
            max_trim = max(pump_trims)
            min_trim = min(pump_trims)
            max_trim_id, max_trim_head_coeffs, max_trim_bep_flow, max_trim_bep_head = PumpTrim.objects.filter(
                pump__series="CI",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=max_trim
            ).values_list(
                "marketing_data__id",
                "marketing_data__headcoeffs",
                "marketing_data__bep_flow",
                "marketing_data__bep_head",
            )[
                0
            ]
            min_trim_head_coeffs, = PumpTrim.objects.filter(
                pump__series="CI",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=min_trim
            ).values_list(
                "marketing_data__headcoeffs",
            )[0]

            max_trim_bep_flow = max_trim_bep_flow*flowunitconversionfactor
            max_trim_bep_head = max_trim_bep_head*headunitconversionfactor
            # print(f"max_trim_id: {max_trim_id}")
            max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.6*max_trim_bep_flow)
            # print(f"max_trim_head_coeffs: {max_trim_head_coeffs}")
            # print(f"min_trim_head_coeffs: {min_trim_head_coeffs}")
            max_poly = np.poly1d(max_trim_head_coeffs)
            min_poly = np.poly1d(min_trim_head_coeffs)
            max_trim_flow_pts = np.linspace(5, max_trim_max_flow, 30)
            max_trim_head_pts = max_poly(max_trim_flow_pts)
            cutoff_curve = np.poly1d(np.flip(P.polyfit([0, max_trim_max_flow], [0, max_poly(max_trim_max_flow)], 2)))
            # print(f"min_poly: \n{min_poly}\ncutoff_curve: \n{cutoff_curve}")
            # find roots
            x_0 = (min_poly - cutoff_curve).roots
            # print(f"roots:{x_0}")
            # print(f"max_flow:{max_trim_max_flow}")
            # select roots in specific range only
            min_trim_max_flow = min(np.real(x_0[(x_0 > 0) & (x_0 < max_trim_max_flow*1.1) & np.isreal(x_0)]))
            # print(f"root:{min_trim_max_flow}")
            
            min_trim_flow_pts = np.linspace(min_trim_max_flow, 5, 30)
            min_trim_head_pts = min_poly(min_trim_flow_pts)

            plot_flows = np.append(max_trim_flow_pts, min_trim_flow_pts)
            plot_flows_metric = plot_flows*0.0630902
            plot_heads = np.append(max_trim_head_pts, min_trim_head_pts)
            plot_heads_metric = plot_heads*0.3048
            plot_heads_kpa = plot_heads*2.98898
            plot_data = np.column_stack((plot_flows, plot_heads))
            plot_data_metric = np.column_stack((plot_flows_metric, plot_heads_metric))
            plot_data_kpa = np.column_stack((plot_flows, plot_heads_kpa))

            temp_model = "a"+str(model)
            if "CI" not in return_pump_data:
                return_pump_data["CI"] = {}
            if temp_model not in return_pump_data["CI"]:
                return_pump_data["CI"][temp_model] = {}
            if design not in return_pump_data["CI"][temp_model]:
                return_pump_data["CI"][temp_model][design] = {}
            if speed not in return_pump_data["CI"][temp_model][design]:
                return_pump_data["CI"][temp_model][design][speed] = {}
            
            # return_pump_data["CI"][temp_model][design][speed]["max_coeffs"] = max_trim_head_coeffs
            # return_pump_data["CI"][temp_model][design][speed]["min_coeffs"] = min_trim_head_coeffs
            # return_pump_data["CI"][temp_model][design][speed]["max_flow"] = max_trim_max_flow

            if speed in [1160, 1760, 3500]:
                return_pump_data["CI"][temp_model][design][speed]["plot_data"] = plot_data.tolist()
            else:
                return_pump_data["CI"][temp_model][design][speed]["plot_data_metric"] = plot_data_metric.tolist()

            return_pump_data["CI"][temp_model][design][speed]["plot_data_kpa"] = plot_data_kpa.tolist()
            return_pump_data["CI"][temp_model][design][speed]["label_location"] = [max_trim_bep_flow, (max_poly(max_trim_max_flow)+max_trim_bep_head*1.5)/2.5]
    
    for model, design in KV_pumps:
        pump_speeds = list(
            Pump.objects.filter(series="KV", pump_model=model, design_iteration=design)
            .values_list("speed", flat=True)
        )
        # print(f"model: KV{model}{design}")
        for speed in pump_speeds:
            pump_trims = list(PumpTrim.objects.filter(
                pump__series="KV",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
            ).values_list("trim", flat=True))
            # print(f"trims:{pump_trims} speed:{speed}")
            max_trim = max(pump_trims)
            min_trim = min(pump_trims)
            max_trim_id, max_trim_head_coeffs, max_trim_bep_flow, max_trim_bep_head = PumpTrim.objects.filter(
                pump__series="KV",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=max_trim
            ).values_list(
                "marketing_data__id",
                "marketing_data__headcoeffs",
                "marketing_data__bep_flow",
                "marketing_data__bep_head",
            )[
                0
            ]
            min_trim_head_coeffs, = PumpTrim.objects.filter(
                pump__series="KV",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=min_trim
            ).values_list(
                "marketing_data__headcoeffs",
            )[0]

            max_trim_bep_flow = max_trim_bep_flow*flowunitconversionfactor
            max_trim_bep_head = max_trim_bep_head*headunitconversionfactor
            # print(f"max_trim_id: {max_trim_id}")
            if str(model)+str(speed) in ["60071160", "60071450", "60071760", "60072900", "60073500"]:
                max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.4*max_trim_bep_flow)
            elif str(model)+str(speed) in ["60111160", "60111450", "60111760", "80111160", "80111450", "80111760", ]:
                max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.5*max_trim_bep_flow)
            else:
                max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.6*max_trim_bep_flow)

            # print(f"max_trim_head_coeffs: {max_trim_head_coeffs}")
            # print(f"min_trim_head_coeffs: {min_trim_head_coeffs}")
            max_poly = np.poly1d(max_trim_head_coeffs)
            min_poly = np.poly1d(min_trim_head_coeffs)
            max_trim_flow_pts = np.linspace(5, max_trim_max_flow, 30)
            max_trim_head_pts = max_poly(max_trim_flow_pts)
            cutoff_curve = np.poly1d(np.flip(P.polyfit([0, max_trim_max_flow], [0, max_poly(max_trim_max_flow)], 2)))
            # print(f"min_poly: \n{min_poly}\ncutoff_curve: \n{cutoff_curve}")
            # find roots
            x_0 = (min_poly - cutoff_curve).roots
            # print(f"roots:{x_0}")
            # select roots in specific range only
            min_trim_max_flow = min(np.real(x_0[(x_0 > 0) & (x_0 < max_trim_max_flow*1.1) & np.isreal(x_0)]))
            # print(f"max_flow:{max_trim_max_flow}")
            # print(f"root:{min_trim_max_flow}")
            
            min_trim_flow_pts = np.linspace(min_trim_max_flow, 5, 30)
            min_trim_head_pts = min_poly(min_trim_flow_pts)

            plot_flows = np.append(max_trim_flow_pts, min_trim_flow_pts)
            plot_flows_metric = plot_flows*0.0630902
            plot_heads = np.append(max_trim_head_pts, min_trim_head_pts)
            plot_heads_metric = plot_heads*0.3048
            plot_heads_kpa = plot_heads*2.98898
            plot_data = np.column_stack((plot_flows, plot_heads))
            plot_data_metric = np.column_stack((plot_flows_metric, plot_heads_metric))
            plot_data_kpa = np.column_stack((plot_flows, plot_heads_kpa))

            temp_model = "a"+str(model)
            if "KV" not in return_pump_data:
                return_pump_data["KV"] = {}
            if temp_model not in return_pump_data["KV"]:
                return_pump_data["KV"][temp_model] = {}
            if design not in return_pump_data["KV"][temp_model]:
                return_pump_data["KV"][temp_model][design] = {}
            if speed not in return_pump_data["KV"][temp_model][design]:
                return_pump_data["KV"][temp_model][design][speed] = {}
            
            # return_pump_data["KV"][temp_model][design][speed]["max_coeffs"] = max_trim_head_coeffs
            # return_pump_data["KV"][temp_model][design][speed]["min_coeffs"] = min_trim_head_coeffs
            # return_pump_data["KV"][temp_model][design][speed]["max_flow"] = max_trim_max_flow

            if speed in [1160, 1760, 3500]:
                return_pump_data["KV"][temp_model][design][speed]["plot_data"] = plot_data.tolist()
            else:
                return_pump_data["KV"][temp_model][design][speed]["plot_data_metric"] = plot_data_metric.tolist()

            return_pump_data["KV"][temp_model][design][speed]["plot_data_kpa"] = plot_data_kpa.tolist()
            return_pump_data["KV"][temp_model][design][speed]["label_location"] = [max_trim_bep_flow, (max_poly(max_trim_max_flow)+max_trim_bep_head*1.5)/2.5]

    for model, design in KS_pumps:
        pump_speeds = list(
            Pump.objects.filter(series="KS", pump_model=model, design_iteration=design)
            .values_list("speed", flat=True)
        )
        # print(f"model:{model}{design} speeds: {pump_speeds}")
        for speed in pump_speeds:
            pump_trims = list(PumpTrim.objects.filter(
                pump__series="KS",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
            ).values_list("trim", flat=True))
            # print(f"trims:{pump_trims}")
            max_trim = max(pump_trims)
            min_trim = min(pump_trims)
            max_trim_id, max_trim_head_coeffs, max_trim_bep_flow, max_trim_bep_head = PumpTrim.objects.filter(
                pump__series="KS",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=max_trim
            ).values_list(
                "marketing_data__id",
                "marketing_data__headcoeffs",
                "marketing_data__bep_flow",
                "marketing_data__bep_head",
            )[
                0
            ]
            min_trim_head_coeffs, = PumpTrim.objects.filter(
                pump__series="KS",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=min_trim
            ).values_list(
                "marketing_data__headcoeffs",
            )[0]

            max_trim_bep_flow = max_trim_bep_flow*flowunitconversionfactor
            max_trim_bep_head = max_trim_bep_head*headunitconversionfactor
            # print(f"max_trim_id: {max_trim_id}")
            if str(model)+str(speed) in ["60071160", "60071450", "60071760", "60072900", "60073500"]:
                max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.4*max_trim_bep_flow)
            elif str(model)+str(speed) in ["60111160", "60111450", "60111760", "80111160", "80111450", "80111760", ]:
                max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.5*max_trim_bep_flow)
            else:
                max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.6*max_trim_bep_flow)

            # print(f"max_trim_head_coeffs: {max_trim_head_coeffs}")
            # print(f"min_trim_head_coeffs: {min_trim_head_coeffs}")
            max_poly = np.poly1d(max_trim_head_coeffs)
            min_poly = np.poly1d(min_trim_head_coeffs)
            max_trim_flow_pts = np.linspace(5, max_trim_max_flow, 30)
            max_trim_head_pts = max_poly(max_trim_flow_pts)
            cutoff_curve = np.poly1d(np.flip(P.polyfit([0, max_trim_max_flow], [0, max_poly(max_trim_max_flow)], 2)))
            # print(f"min_poly: \n{min_poly}\ncutoff_curve: \n{cutoff_curve}")
            # find roots
            x_0 = (min_poly - cutoff_curve).roots
            # print(f"roots:{x_0}")
            # select roots in specific range only
            min_trim_max_flow = min(np.real(x_0[(x_0 > 0) & (x_0 < max_trim_max_flow*1.1) & np.isreal(x_0)]))
            # print(f"max_flow:{max_trim_max_flow}")
            # print(f"root:{min_trim_max_flow}")
            
            min_trim_flow_pts = np.linspace(min_trim_max_flow, 5, 30)
            min_trim_head_pts = min_poly(min_trim_flow_pts)

            plot_flows = np.append(max_trim_flow_pts, min_trim_flow_pts)
            plot_flows_metric = plot_flows*0.0630902
            plot_heads = np.append(max_trim_head_pts, min_trim_head_pts)
            plot_heads_metric = plot_heads*0.3048
            plot_heads_kpa = plot_heads*2.98898
            plot_data = np.column_stack((plot_flows, plot_heads))
            plot_data_metric = np.column_stack((plot_flows_metric, plot_heads_metric))
            plot_data_kpa = np.column_stack((plot_flows, plot_heads_kpa))

            temp_model = "a"+str(model)
            if "KS" not in return_pump_data:
                return_pump_data["KS"] = {}
            if temp_model not in return_pump_data["KS"]:
                return_pump_data["KS"][temp_model] = {}
            if design not in return_pump_data["KS"][temp_model]:
                return_pump_data["KS"][temp_model][design] = {}
            if speed not in return_pump_data["KS"][temp_model][design]:
                return_pump_data["KS"][temp_model][design][speed] = {}
            
            # return_pump_data["KS"][temp_model][design][speed]["max_coeffs"] = max_trim_head_coeffs
            # return_pump_data["KS"][temp_model][design][speed]["min_coeffs"] = min_trim_head_coeffs
            # return_pump_data["KS"][temp_model][design][speed]["max_flow"] = max_trim_max_flow

            if speed in [1160, 1760, 3500]:
                return_pump_data["KS"][temp_model][design][speed]["plot_data"] = plot_data.tolist()
            else:
                return_pump_data["KS"][temp_model][design][speed]["plot_data_metric"] = plot_data_metric.tolist()

            return_pump_data["KS"][temp_model][design][speed]["plot_data_kpa"] = plot_data_kpa.tolist()
            return_pump_data["KS"][temp_model][design][speed]["label_location"] = [max_trim_bep_flow, (max_poly(max_trim_max_flow)+max_trim_bep_head*1.5)/2.5]
    
    for model, design in HS_pumps:
        pump_speeds = list(
            Pump.objects.filter(series="HS", pump_model=model, design_iteration=design)
            .values_list("speed", flat=True)
        )
        # print(f"model:{model}{design} speeds: {pump_speeds}")
        for speed in pump_speeds:
            pump_trims = list(PumpTrim.objects.filter(
                pump__series="HS",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
            ).values_list("trim", flat=True))
            # print(f"trims:{pump_trims}")
            max_trim = max(pump_trims)
            min_trim = min(pump_trims)
            max_trim_id, max_trim_head_coeffs, max_trim_bep_flow, max_trim_bep_head = PumpTrim.objects.filter(
                pump__series="HS",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=max_trim
            ).values_list(
                "marketing_data__id",
                "marketing_data__headcoeffs",
                "marketing_data__bep_flow",
                "marketing_data__bep_head",
            )[
                0
            ]
            min_trim_head_coeffs, = PumpTrim.objects.filter(
                pump__series="HS",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=min_trim
            ).values_list(
                "marketing_data__headcoeffs",
            )[0]

            max_trim_bep_flow = max_trim_bep_flow*flowunitconversionfactor
            max_trim_bep_head = max_trim_bep_head*headunitconversionfactor
            # print(f"max_trim_id: {max_trim_id}")
            if str(model)+str(speed) in ["60071160", "60071450", "60071760", "60072900", "60073500"]:
                max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.4*max_trim_bep_flow)
            elif str(model)+str(speed) in ["60111160", "60111450", "60111760", "80111160", "80111450", "80111760", ]:
                max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.5*max_trim_bep_flow)
            else:
                max_trim_max_flow = min(max(MarketingCurveData.objects.filter(curveid=max_trim_id).values_list("flow", flat=True))*flowunitconversionfactor, 1.6*max_trim_bep_flow)

            # print(f"max_trim_head_coeffs: {max_trim_head_coeffs}")
            # print(f"min_trim_head_coeffs: {min_trim_head_coeffs}")
            max_poly = np.poly1d(max_trim_head_coeffs)
            min_poly = np.poly1d(min_trim_head_coeffs)
            max_trim_flow_pts = np.linspace(5, max_trim_max_flow, 30)
            max_trim_head_pts = max_poly(max_trim_flow_pts)
            cutoff_curve = np.poly1d(np.flip(P.polyfit([0, max_trim_max_flow], [0, max_poly(max_trim_max_flow)], 2)))
            # print(f"min_poly: \n{min_poly}\ncutoff_curve: \n{cutoff_curve}")
            # find roots
            x_0 = (min_poly - cutoff_curve).roots
            # print(f"roots:{x_0}")
            # select roots in specific range only
            min_trim_max_flow = min(np.real(x_0[(x_0 > 0) & (x_0 < max_trim_max_flow*1.1) & np.isreal(x_0)]))
            # print(f"max_flow:{max_trim_max_flow}")
            # print(f"root:{min_trim_max_flow}")
            
            min_trim_flow_pts = np.linspace(min_trim_max_flow, 5, 30)
            min_trim_head_pts = min_poly(min_trim_flow_pts)

            plot_flows = np.append(max_trim_flow_pts, min_trim_flow_pts)
            plot_flows_metric = plot_flows*0.0630902
            plot_heads = np.append(max_trim_head_pts, min_trim_head_pts)
            plot_heads_metric = plot_heads*0.3048
            plot_heads_kpa = plot_heads*2.98898
            plot_data = np.column_stack((plot_flows, plot_heads))
            plot_data_metric = np.column_stack((plot_flows_metric, plot_heads_metric))
            plot_data_kpa = np.column_stack((plot_flows, plot_heads_kpa))

            temp_model = "a"+str(model)
            if "HS" not in return_pump_data:
                return_pump_data["HS"] = {}
            if temp_model not in return_pump_data["HS"]:
                return_pump_data["HS"][temp_model] = {}
            if design not in return_pump_data["HS"][temp_model]:
                return_pump_data["HS"][temp_model][design] = {}
            if speed not in return_pump_data["HS"][temp_model][design]:
                return_pump_data["HS"][temp_model][design][speed] = {}
            
            # return_pump_data["HS"][temp_model][design][speed]["max_coeffs"] = max_trim_head_coeffs
            # return_pump_data["HS"][temp_model][design][speed]["min_coeffs"] = min_trim_head_coeffs
            # return_pump_data["HS"][temp_model][design][speed]["max_flow"] = max_trim_max_flow

            if speed in [1160, 1760, 3500]:
                return_pump_data["HS"][temp_model][design][speed]["plot_data"] = plot_data.tolist()
            else:
                return_pump_data["HS"][temp_model][design][speed]["plot_data_metric"] = plot_data_metric.tolist()

            return_pump_data["HS"][temp_model][design][speed]["plot_data_kpa"] = plot_data_kpa.tolist()
            return_pump_data["HS"][temp_model][design][speed]["label_location"] = [max_trim_bep_flow, (max_poly(max_trim_max_flow)+max_trim_bep_head*1.5)/2.5]
    # print(return_pump_data)
    context = {
        "data": return_pump_data
    }
    return JsonResponse(context, safe=False)

