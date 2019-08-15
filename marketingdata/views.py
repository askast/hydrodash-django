import json
import numpy as np
from scipy.interpolate import UnivariateSpline

from django.http import JsonResponse
from django.views.generic.base import TemplateView
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.db.models import Q

from .models import MarketingCurveDetail, MarketingCurveData
from pump.models import Pump, PumpTrim
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
        maxhead = -20
        index = 0
        for index, headpoint in enumerate(np.flip(head)):
            if headpoint > maxhead:
                maxhead = headpoint
            else:
                break

        maxheadindex = max_index - index

        for index in range(0, maxheadindex):
            head[index] = maxhead

        head_poly = np.poly1d(np.polyfit(flow, head, 6))
        head = head_poly(flow)
        headcoeffs = list(
            np.polyfit(
                flow / flowunitconversionfactor, head / headunitconversionfactor, 6
            )
        )
    else:
        head_poly = np.poly1d(np.polyfit(flow, head, 6))
        head = head_poly(flow)
        headcoeffs = list(
            np.polyfit(
                flow / flowunitconversionfactor, head / headunitconversionfactor, 6
            )
        )

    if bearinglossremoval:
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

    if targeteff:
        targeteff = float(targeteff)
        effmultiplier = targeteff / (bep_eff * 100)
        eff = eff * effmultiplier

    if bepshift:
        shiftflow = []
        for index, flowpoint in enumerate(flow):
            if index <= bep_index:
                shiftflow.append(flowpoint - bep_flow * 0.05 * index / bep_index)
            else:
                shiftflow.append(
                    flowpoint
                    - bep_flow * 0.05 * ((index - max_index) / (bep_index - max_index))
                )

        shift_eff_poly = UnivariateSpline(np.array(shiftflow), eff, s=0.000001)
        eff = shift_eff_poly(flow)

    powerpts = head * flow / (eff * 367)
    power_poly = np.poly1d(
        np.polyfit(flow[int(0.05 * max_index) :], powerpts[int(0.05 * max_index) :], 6)
    )
    power = power_poly(flow)
    eff = head * flow / (power * 367)

    effcoeffs = list(np.polyfit(flow / flowunitconversionfactor, eff, 6))
    powercoeffs = list(np.polyfit(flow / flowunitconversionfactor, power/ powerunitconversionfactor, 6))
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
    # populatePumps()

    return JsonResponse(context)


def getPumpModels(request):
    """

    :param request: 

    """
    series = request.GET.get("series", None)
    pumpmodels = list(
        Pump.objects.filter(series=series)
        .order_by('pump_model')
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
        PumpTrim.objects.filter(pump__series=series, pump__pump_model=pumpmodel, pump__design_iteration=designit, pump__speed=rpm)
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
    curvepowercoefficients = json.loads(request.POST.get("curvepowercoefficients", None))
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
    power_120 = power[int(bep_index * 1.2)]
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
        powercoeffs=curvepowercoefficients
    )
    curveDetailObj.save()

    if series and pumpmodel and designit and rpm and trim:
        pumptrim = PumpTrim.objects.filter(
            pump__series=series,
            pump__pump_model=pumpmodel,
            pump__design_iteration=designit,
            pump__speed=rpm, trim=trim)
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
        elif flow_units == "Millimeters":
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
    elif flow_units == "Millimeters":
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
        )
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


def populatePumps():
    pumpstring = """
    KV	1506	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    KV	2006	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    KV	3006	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    KV	1507	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    KV	2007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    KV	3007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.875, 6.5, 6.0, 5.5
    KV	5007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    KV	6007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75
    KV	2009	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    KV	3009	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    KV	4009	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    KV	6009	D	1160, 1450, 1760	9.5, 9.0, 8.5, 7.75, 7.00
    KV	2011	D	1160, 1450, 1760	11.25, 10.5, 9.75, 9.0, 8.25
    KV	3011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    KV	4011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    KV	6011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    KV	8011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    KV	3013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    KV	4013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    KV	6013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    KV	8013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    KS	1506	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    KS	2006	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    KS	3006	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    KS	1507	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    KS	2007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    KS	3007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.875, 6.5, 6.0, 5.5
    KS	5007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    KS	6007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75
    KS	2009	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    KS	3009	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    KS	4009	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    KS	6009	D	1160, 1450, 1760	9.5, 9.0, 8.5, 7.75, 7.00
    KS	2011	D	1160, 1450, 1760	11.25, 10.5, 9.75, 9.0, 8.25
    KS	3011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    KS	4011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    KS	6011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    KS	8011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    KS	3013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    KS	4013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    KS	6013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    KS	8013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    FI	1206	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    FI	1506	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    FI	2506	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    FI	1207	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    FI	1507	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    FI	2007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    FI	2507	D	1160, 1450, 1760, 2900, 3500	7.25, 6.875, 6.5, 6.0, 5.5
    FI	3007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    FI	4007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    FI	5007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75
    FI	1209	D	1160, 1450, 1760, 2900, 3500	9.5, 8.8, 8.1, 7.4, 6.7
    FI	1509	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    FI	2009	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    FI	2509	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    FI	3009	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    FI	4009	D	1160, 1450, 1760	9.5, 9.0, 8.25, 7.5, 6.75
    FI	5009	D	1160, 1450, 1760	9.5, 9.0, 8.5, 7.75, 7.00
    FI	6009	D	1160, 1450, 1760	9.5, 9.0, 8.5, 8.0, 7.0
    FI	1511	D	1160, 1450, 1760	11.25, 10.5, 9.75, 9.0, 8.25
    FI	2511	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    FI	3011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    FI	4011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    FI	5011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    FI	6011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    FI	2013	D	1160, 1450, 1760	13.5, 12.63, 11.75, 10.88, 10.0
    FI	2513	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    FI	3013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    FI	4013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    FI	5013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    FI	6013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    FI	8013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    CI	1206	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    CI	1506	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    CI	2506	D	1450, 1760, 2900, 3500	6.25, 5.75, 5.25, 4.75, 4.25
    CI	1207	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    CI	1507	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    CI	2007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    CI	2507	D	1160, 1450, 1760, 2900, 3500	7.25, 6.875, 6.5, 6.0, 5.5
    CI	3007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    CI	4007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75, 5.25
    CI	5007	D	1160, 1450, 1760, 2900, 3500	7.25, 6.75, 6.25, 5.75
    CI	1209	D	1160, 1450, 1760, 2900, 3500	9.5, 8.8, 8.1, 7.4, 6.7
    CI	1509	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    CI	2009	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    CI	2509	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    CI	3009	D	1160, 1450, 1760, 2900, 3500	9.5, 9.0, 8.25, 7.5, 6.75
    CI	4009	D	1160, 1450, 1760	9.5, 9.0, 8.25, 7.5, 6.75
    CI	5009	D	1160, 1450, 1760	9.5, 9.0, 8.5, 7.75, 7.00
    CI	6009	D	1160, 1450, 1760	9.5, 9.0, 8.5, 8.0, 7.0
    CI	1511	D	1160, 1450, 1760	11.25, 10.5, 9.75, 9.0, 8.25
    CI	2511	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    CI	3011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    CI	4011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    CI	5011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    CI	6011	D	1160, 1450, 1760	11.00, 10.25, 9.5, 8.75, 8.0
    CI	2013	D	1160, 1450, 1760	13.5, 12.63, 11.75, 10.88, 10.0
    CI	2513	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    CI	3013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    CI	4013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    CI	5013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    CI	6013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5
    CI	8013	D	1160, 1450, 1760	13.5, 12.5, 11.5, 10.5, 9.5"""
    Pump.objects.all().delete()
    PumpTrim.objects.all().delete()
    for line in pumpstring.strip().split("\n"):
        series, pumpmodel, design, speeds, trims = line.split("\t")
        for speed in speeds.split(", "):
            pumpObj = Pump(
                series=series.strip(),
                pump_model=pumpmodel,
                design_iteration=design,
                speed=speed,
            )
            pumpObj.save()
            for trim in trims.split(", "):
                trimObj = PumpTrim(pump=pumpObj, trim=trim)
                trimObj.save()
    curvenumbers_string = """
    KV-2006D	3500	PC-4141
KV-2006D	1760	PC-4143
KV-2006D	2900	PC-4142
KV-2006D	1450	PC-4144
KV-3006D	3500	PC-4140
KV-3006D	1760	PC-4138
KV-3006D	2900	PC-4139
KV-3006D	1450	PC-4137
KV-1507D	3500	PC-4153
KV-1507D	1760	PC-4151
KV-1507D	2900	PC-4152
KV-1507D	1450	PC-4150
KV-1507D	1160	PC-4149
KV-2007D	3500	PC-4158
KV-2007D	1760	PC-4156
KV-2007D	2900	PC-4157
KV-2007D	1450	PC-4155
KV-2007D	1160	PC-4154
KV-3007D	3500	PC-4163
KV-3007D	1760	PC-4161
KV-3007D	2900	PC-4162
KV-3007D	1450	PC-4160
KV-3007D	1160	PC-4159
KV-2009D	3500	PC-4173
KV-2009D	1760	PC-4171
KV-2009D	2900	PC-4172
KV-2009D	1450	PC-4170
KV-2009D	1160	PC-4169
KV-5007D	3500	PC-4168
KV-5007D	1760	PC-4166
KV-5007D	2900	PC-4167
KV-5007D	1450	PC-4165
KV-5007D	1160	PC-4164
KV-1506D	3500	PC-4148
KV-1506D	1760	PC-4146
KV-1506D	2900	PC-4147
KV-1506D	1450	PC-4145
KV-6009D	3500	PC-4178
KV-6009D	1760	PC-4176
KV-6009D	2900	PC-4177
KV-6009D	1450	PC-4175
KV-6009D	1160	PC-4174
"""