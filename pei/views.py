import os
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic.base import TemplateView
import math
import numpy as np
from scipy import interpolate

from .utils import calculateCirculatorPEI
from profiles.models import Profile
from testdata.models import ReducedPumpTestDetails, ReducedPumpTestData


# Create your views here.
class PeiCalcuatorView(TemplateView):
    template_name = "pei/peicalculator.html"

    def get_context_data(self, **kwargs):

        context = {
            "name": self.request.user.get_full_name(),
            "servername": os.environ.get("USERNAME"),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "PEI Calculator",
        }
        return context


def calculatePei(request):
    bep_flow = float(request.POST.get("bep_flow", None))
    bep_head = float(request.POST.get("bep_head", None))
    q_25_max = float(request.POST.get("q_25_max", None))
    q_50_max = float(request.POST.get("q_50_max", None))
    q_75_max = float(request.POST.get("q_75_max", None))
    q_100_max = float(request.POST.get("q_100_max", None))
    h_25_max = float(request.POST.get("h_25_max", None))
    h_50_max = float(request.POST.get("h_50_max", None))
    h_75_max = float(request.POST.get("h_75_max", None))
    h_100_max = float(request.POST.get("h_100_max", None))
    q_25_reduced_test = float(request.POST.get("q_25_reduced_test", None))
    q_50_reduced_test = float(request.POST.get("q_50_reduced_test", None))
    q_75_reduced_test = float(request.POST.get("q_75_reduced_test", None))
    q_100_reduced_test = float(request.POST.get("q_100_reduced_test", None))
    h_25_reduced_test = float(request.POST.get("h_25_reduced_test", None))
    h_50_reduced_test = float(request.POST.get("h_50_reduced_test", None))
    h_75_reduced_test = float(request.POST.get("h_75_reduced_test", None))
    h_100_reduced_test = float(request.POST.get("h_100_reduced_test", None))
    p_25_reduced_test = float(request.POST.get("p_25_reduced_test", None))
    p_50_reduced_test = float(request.POST.get("p_50_reduced_test", None))
    p_75_reduced_test = float(request.POST.get("p_75_reduced_test", None))
    p_100_reduced_test = float(request.POST.get("p_100_reduced_test", None))

    result = calculateCirculatorPEI(bep_flow, bep_head, q_25_max, q_50_max, q_75_max, q_100_max, h_25_max, h_50_max, h_75_max, h_100_max, q_25_reduced_test, q_50_reduced_test, q_75_reduced_test, q_100_reduced_test, h_25_reduced_test, h_50_reduced_test, h_75_reduced_test, h_100_reduced_test, p_25_reduced_test, p_50_reduced_test, p_75_reduced_test, p_100_reduced_test)

    context = {
        "status" : result["status"],
        "pei" : result["PEI"],
        "er" : result["ER"],
    }

    return JsonResponse(context)



class CirculatorPeiTestListView(TemplateView):
    template_name = "pei/circpeitestwizard.html"

    def get_context_data(self, **kwargs):
        context = {
            "name": self.request.user.get_full_name(),
            "servername": os.environ.get("USERNAME"),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "PEI Wizard",
        }
        return context


class CirculatorPeiTest2View(TemplateView):
    template_name = "pei/circpeitestwizard2.html"

    def get_context_data(self, **kwargs):
        testid = self.request.GET.get('testid', None)
        testdetail = ReducedPumpTestDetails.objects.filter(id=testid)
        testname = testdetail.values("testname")[0]['testname']

        context = {
            "name": self.request.user.get_full_name(),
            "servername": os.environ.get("USERNAME"),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "PEI Wizard",
            "testid": testid,
            "testname": testname,
        }
        return context


class CirculatorPeiTest3View(TemplateView):
    template_name = "pei/circpeitestwizard3.html"

    def get_context_data(self, **kwargs):
        test1id = self.request.GET.get('test1id', None)
        test2id = self.request.GET.get('test2id', None)
        test1detail = ReducedPumpTestDetails.objects.filter(id=test1id)
        test1name = test1detail.values("testname")[0]['testname']
        test2detail = ReducedPumpTestDetails.objects.filter(id=test2id)
        test2name = test2detail.values("testname")[0]['testname']

        context = {
            "name": self.request.user.get_full_name(),
            "servername": os.environ.get("USERNAME"),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "PEI Wizard",
            "test1id": test1id,
            "test1name": test1name,
            "test2id": test2id,
            "test2name": test2name,
        }
        return context


def circPeiPointsToTest(request):
    flowunitconversionfactor = 4.402862
    headunitconversionfactor = 3.28084

    testid = request.GET.get('testid', None)
    testdetail = ReducedPumpTestDetails.objects.filter(id=testid)
    testname = testdetail.values("testname")[0]['testname']

    testdata = list(ReducedPumpTestData.objects.filter(
        testid=testdetail[0]).values('flow', 'head', 'power', 'rpm'))

    chart_flow = []
    chart_head = []
    chart_power = []
    chart_eff = []
    table_data = []

    for record in testdata:
        chart_flow.append(float(record['flow']))
        chart_head.append(float(record['head']))
        chart_power.append(float(record['power']))

    for flow, head, power in zip(chart_flow, chart_head, chart_power):
        eff = flow*head/(367*power)*100
        chart_eff.append(eff)

    for index, value in enumerate(chart_flow):
        chart_flow[index] = chart_flow[index]*flowunitconversionfactor
        chart_head[index] = chart_head[index]*headunitconversionfactor
        table_data.append([chart_flow[index], chart_head[index], chart_eff[index], chart_power[index]])

    bep_index = chart_eff.index(max(chart_eff))
    bep_flow = chart_flow[bep_index]
    bep_head = chart_head[bep_index]
    flow_25 = 0.25*bep_flow
    flow_50 = 0.5*bep_flow
    flow_75 = 0.75*bep_flow
    head_25 = (0.8*math.pow(flow_25/bep_flow, 2)+0.2)*bep_head
    head_50 = (0.8*math.pow(flow_50/bep_flow, 2)+0.2)*bep_head
    head_75 = (0.8*math.pow(flow_75/bep_flow, 2)+0.2)*bep_head

    points_to_test_flow = [flow_25, flow_50, flow_75, bep_flow]
    points_to_test_head = [head_25, head_50, head_75, bep_head]

    context = {
        "testid": testid,
        "testname": testname,
        "chartflow": chart_flow,
        "charthead": chart_head,
        "testpointsflow": points_to_test_flow,
        "testpointshead": points_to_test_head,
    }
    return JsonResponse(context)


def circPeiData(request):
    flowunitconversionfactor = 4.402862
    headunitconversionfactor = 3.28084

    test1id = request.GET.get('test1id', None)
    test1detail = ReducedPumpTestDetails.objects.filter(id=test1id)
    test1name = test1detail.values("testname")[0]['testname']

    test1data = list(ReducedPumpTestData.objects.filter(
        testid=test1detail[0]).values('flow', 'head', 'power'))

    test1_flow = []
    test1_head = []
    test1_power = []
    test1_eff = []

    test2id = request.GET.get('test2id', None)
    test2detail = ReducedPumpTestDetails.objects.filter(id=test2id)
    test2name = test2detail.values("testname")[0]['testname']

    test2data = list(ReducedPumpTestData.objects.filter(
        testid=test2detail[0]).values('flow', 'head', 'power'))

    test2_flow = []
    test2_head = []
    test2_power = []
    test2_eff = []

    for record in test1data:
        test1_flow.append(float(record['flow']))
        test1_head.append(float(record['head']))
        test1_power.append(float(record['power']))

    for flow, head, power in zip(test1_flow, test1_head, test1_power):
        eff = flow*head/(367*power)*100
        test1_eff.append(eff)

    for index, value in enumerate(test1_flow):
        test1_flow[index] = test1_flow[index]*flowunitconversionfactor
        test1_head[index] = test1_head[index]*headunitconversionfactor

    bep_index = test1_eff.index(max(test1_eff))
    bep_flow = test1_flow[bep_index]
    bep_head = test1_head[bep_index]
    flow_25 = 0.25*bep_flow
    flow_50 = 0.5*bep_flow
    flow_75 = 0.75*bep_flow
    head_25 = (0.8*math.pow(flow_25/bep_flow, 2)+0.2)*bep_head
    head_50 = (0.8*math.pow(flow_50/bep_flow, 2)+0.2)*bep_head
    head_75 = (0.8*math.pow(flow_75/bep_flow, 2)+0.2)*bep_head

    points_to_test_flow = [flow_25, flow_50, flow_75, bep_flow]
    points_to_test_head = [head_25, head_50, head_75, bep_head]

    for record in test2data:
        test2_flow.append(float(record['flow']))
        test2_head.append(float(record['head']))
        test2_power.append(float(record['power']))

    for flow, head, power in zip(test2_flow, test2_head, test2_power):
        eff = flow*head/(367*power)*200
        test2_eff.append(eff)

    for index, value in enumerate(test2_flow):
        test2_flow[index] = test2_flow[index]*flowunitconversionfactor
        test2_head[index] = test2_head[index]*headunitconversionfactor

    closest_indices = []

    for compare_flow in points_to_test_flow:
        closest_index = 0
        min_gap = abs(compare_flow - test2_flow[0])
        for index, value in enumerate(test2_flow):
            gap = abs(compare_flow - value)
            if gap < min_gap:
                min_gap = gap
                closest_index = index
        closest_indices.append(closest_index)
    
    test2_flow_25 = test2_flow[closest_indices[0]]
    test2_head_25 = test2_head[closest_indices[0]]
    test2_power_25 = test2_power[closest_indices[0]]
    test2_flow_50 = test2_flow[closest_indices[1]]
    test2_head_50 = test2_head[closest_indices[1]]
    test2_power_50 = test2_power[closest_indices[1]]
    test2_flow_75 = test2_flow[closest_indices[2]]
    test2_head_75 = test2_head[closest_indices[2]]
    test2_power_75 = test2_power[closest_indices[2]]
    test2_flow_bep = test2_flow[closest_indices[3]]
    test2_head_bep = test2_head[closest_indices[3]]
    test2_power_bep = test2_power[closest_indices[3]]

    approved_test2_head = []
    approved_test2_flow = []
    approved_test2_power = []
    if test2_head_25 > 0.9*head_25:
        approved_test2_head.append(test2_head_25)
        approved_test2_flow.append(test2_flow_25)
        approved_test2_power.append(test2_power_25)
    else:
        approved_test2_head.append(None)
        approved_test2_flow.append(None)
        approved_test2_power.append(None)
    if test2_head_50 > 0.9*head_50:
        approved_test2_head.append(test2_head_50)
        approved_test2_flow.append(test2_flow_50)
        approved_test2_power.append(test2_power_50)
    else:
        approved_test2_head.append(None)
        approved_test2_flow.append(None)
        approved_test2_power.append(None)
    if test2_head_75 > 0.9*head_75:
        approved_test2_head.append(test2_head_75)
        approved_test2_flow.append(test2_flow_75)
        approved_test2_power.append(test2_power_75)
    else:
        approved_test2_head.append(None)
        approved_test2_flow.append(None)
        approved_test2_power.append(None)
    if test2_head_bep > 0.9*bep_head:
        approved_test2_head.append(test2_head_bep)
        approved_test2_flow.append(test2_flow_bep)
        approved_test2_power.append(test2_power_bep)
    else:
        approved_test2_head.append(None)
        approved_test2_flow.append(None)
        approved_test2_power.append(None)

    test1_head_func = interpolate.interp1d(test1_flow, test1_head, kind='linear')
    test1_head_25 = test1_head_func(flow_25)
    test1_head_50 = test1_head_func(flow_50)
    test1_head_75 = test1_head_func(flow_75)

    if None not in approved_test2_flow:
        PEI_result = calculateCirculatorPEI(bep_flow, bep_head, flow_25, flow_50, flow_75, bep_flow,
            test1_head_25, test1_head_50, test1_head_75, bep_head, test2_flow_25, test2_flow_50,
            test2_flow_75, test2_flow_bep, test2_head_25, test2_head_50, test2_head_75, test2_head_bep,
            test2_power_25, test2_power_50, test2_power_75, test2_power_bep)
    else:
        PEI_result = {
            "status": "failed",
            "PEI": 0,
            "ER": 0,
        }
    
    
    test2_flow_red = []
    test2_head_red = []
    test2_flow_green = []
    test2_head_green = []
    for flow, head in zip(test2_flow, test2_head):
        if flow in approved_test2_flow:
            test2_flow_green.append(flow)
            test2_head_green.append(head)
        else:
            test2_flow_red.append(flow)
            test2_head_red.append(head)



    context = {
        "test1id": test1id,
        "test1name": test1name,
        "test2id": test2id,
        "test2name": test2name,
        "test1flow": test1_flow,
        "test1head": test1_head,
        "testpointsflow": points_to_test_flow,
        "testpointshead": points_to_test_head,
        "test2flowgreen": test2_flow_green,
        "test2headgreen": test2_head_green,
        "test2flowred": test2_flow_red,
        "test2headred": test2_head_red,
        "peiresult": PEI_result,
    }
    return JsonResponse(context)
