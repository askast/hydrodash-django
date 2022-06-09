import os
# from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic.base import TemplateView
import math
# import numpy as np
# from numpy.lib.function_base import place
from numpy.polynomial.polynomial import Polynomial
from scipy import interpolate
from scipy.optimize import minimize_scalar

from .utils import calculateCirculatorPEI
# from profiles.models import Profile
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

    result = calculateCirculatorPEI(bep_flow, bep_head, q_25_max, q_50_max, q_75_max, q_100_max, h_25_max, h_50_max, h_75_max, h_100_max, 0, 0, 0, 0, q_25_reduced_test, q_50_reduced_test, q_75_reduced_test, q_100_reduced_test, h_25_reduced_test, h_50_reduced_test, h_75_reduced_test, h_100_reduced_test, p_25_reduced_test, p_50_reduced_test, p_75_reduced_test, p_100_reduced_test)

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



    eff_poly = Polynomial.fit(chart_flow, chart_eff, 6)
    head_poly = Polynomial.fit(chart_flow, chart_head, 6)
    eff_poly_reversed = lambda x: eff_poly(x)*-1
    bep = minimize_scalar(eff_poly_reversed, bounds=(min(chart_flow), max(chart_flow)), method='bounded')
    # print(f'**\n\nBEP flow: {bep["x"]}\nBEP eff:{eff_poly(bep["x"])} \n\n**')

    # bep_index = test1_eff.index(max(test1_eff))
    bep_flow = bep["x"]
    bep_head = head_poly(bep["x"])

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
    powerunitconversionfactor = 1.34102

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
    calculator_spreadsheet_input_csv = []
    upload_spreadsheet_input_csv = []
    doe_spreadsheet_input_csv = []
    

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
        test1_power[index] = test1_power[index]*powerunitconversionfactor

    eff_poly = Polynomial.fit(test1_flow, test1_eff, 6)
    head_poly = Polynomial.fit(test1_flow, test1_head, 6)
    head_coeffs = head_poly.convert().coef[::-1]
    head_poly_string = "y="
    for i in range(len(head_coeffs)):
        if head_coeffs[i] < 0 and i > 0:
            head_poly_string = head_poly_string[:-1]
        head_poly_string += str(head_coeffs[i])
        if i < len(head_coeffs)-2:
            head_poly_string += "x^"+str(len(head_coeffs)-i-1)+"+"
        elif i < len(head_coeffs)-1:
            head_poly_string += "x+"
    print(f'**\n\nhead_poly: {head_poly_string}\n\n**')
    power_poly = Polynomial.fit(test1_flow, test1_power, 4)
    eff_poly_reversed = lambda x: eff_poly(x)*-1
    bep = minimize_scalar(eff_poly_reversed, bounds=(min(test1_flow), max(test1_flow)), method='bounded')
    # print(f'**\n\nBEP flow: {bep["x"]}\nBEP eff:{eff_poly(bep["x"])} \n\n**')

    # bep_index = test1_eff.index(max(test1_eff))
    bep_flow = bep["x"]
    bep_head = head_poly(bep["x"])
    bep_power = power_poly(bep["x"])
    flow_25 = 0.25*bep_flow
    flow_50 = 0.5*bep_flow
    flow_75 = 0.75*bep_flow
    flow_110 = 1.1*bep_flow
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
        test2_power[index] = test2_power[index]*powerunitconversionfactor

    closest_indices = []

    head_poly_reduced = Polynomial.fit(test2_flow, test2_head, 3)
    head_coeffs_reduced = head_poly_reduced.convert().coef[::-1]
    head_poly_reduced_string = "y="
    for i in range(len(head_coeffs_reduced)):
        if head_coeffs_reduced[i] < 0 and i > 0:
            head_poly_reduced_string = head_poly_reduced_string[:-1]
        head_poly_reduced_string += str(head_coeffs_reduced[i])
        if i < len(head_coeffs_reduced)-2:
            head_poly_reduced_string += "x^"+str(len(head_coeffs_reduced)-i-1)+"+"
        elif i < len(head_coeffs_reduced)-1:
            head_poly_reduced_string += "x+"
    print(f'**\n\nhead_poly_reduced: {head_poly_reduced_string}\n\n**')

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
    if test2_head_50 > 0.2*head_50:
        approved_test2_head.append(test2_head_50)
        approved_test2_flow.append(test2_flow_50)
        approved_test2_power.append(test2_power_50)
    else:
        approved_test2_head.append(None)
        approved_test2_flow.append(None)
        approved_test2_power.append(None)
    if test2_head_75 > 0.2*head_75:
        approved_test2_head.append(test2_head_75)
        approved_test2_flow.append(test2_flow_75)
        approved_test2_power.append(test2_power_75)
    else:
        approved_test2_head.append(None)
        approved_test2_flow.append(None)
        approved_test2_power.append(None)
    if test2_head_bep > 0.2*bep_head:
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
    test1_head_110 = test1_head_func(flow_110)
    
    test1_power_25 = power_poly(flow_25)
    test1_power_50 = power_poly(flow_50)
    test1_power_75 = power_poly(flow_75)
    test1_power_110 = power_poly(flow_110)
    

    if None not in approved_test2_flow:
        PEI_result = calculateCirculatorPEI(bep_flow, bep_head, flow_25, flow_50, flow_75, bep_flow,
            test1_head_25, test1_head_50, test1_head_75, bep_head, 
            test1_power_25, test1_power_50, test1_power_75, bep_power, 
            test2_flow_25, test2_flow_50, test2_flow_75, test2_flow_bep, 
            test2_head_25, test2_head_50, test2_head_75, test2_head_bep,
            test2_power_25, test2_power_50, test2_power_75, test2_power_bep)
        
        calculator_spreadsheet_input_csv.extend([bep_flow, bep_head, power_poly(bep_flow)])
        calculator_spreadsheet_input_csv.extend([0.1*bep_flow, .25*bep_flow, .4*bep_flow, .6*bep_flow, .75*bep_flow, .9*bep_flow, bep_flow, 1.1*bep_flow, 1.2*bep_flow])
        calculator_spreadsheet_input_csv.extend([head_poly(0.1*bep_flow), head_poly(.25*bep_flow), head_poly(.4*bep_flow), head_poly(.6*bep_flow), head_poly(.75*bep_flow), head_poly(.9*bep_flow), bep_head, head_poly(1.1*bep_flow), head_poly(1.2*bep_flow)])
        calculator_spreadsheet_input_csv.extend([power_poly(0.1*bep_flow), power_poly(.25*bep_flow), power_poly(.4*bep_flow), power_poly(.6*bep_flow), power_poly(.75*bep_flow), power_poly(.9*bep_flow), bep_power, power_poly(1.1*bep_flow), power_poly(1.2*bep_flow)])
        calculator_spreadsheet_input_csv.extend([test2_flow_25, test2_flow_50, test2_flow_75, test2_flow_bep])
        calculator_spreadsheet_input_csv.extend([test2_head_25, test2_head_50, test2_head_75, test2_head_bep])
        calculator_spreadsheet_input_csv.extend([test2_power_25, test2_power_50, test2_power_75, test2_power_bep])
        # calculator_spreadsheet_input_csv.extend([bep_flow, bep_head, power_poly(bep_flow)])
        # calculator_spreadsheet_input_csv.extend([0.1*bep_flow, .25*bep_flow, .4*bep_flow, .6*bep_flow, .75*bep_flow, .9*bep_flow, bep_flow, 1.1*bep_flow, 1.2*bep_flow])
        # calculator_spreadsheet_input_csv.extend([head_poly(0.1*bep_flow), head_poly(.25*bep_flow), head_poly(.4*bep_flow), head_poly(.6*bep_flow), head_poly(.75*bep_flow), head_poly(.9*bep_flow), bep_head, head_poly(1.1*bep_flow), head_poly(1.2*bep_flow)])
        # calculator_spreadsheet_input_csv.extend([power_poly(0.1*bep_flow), power_poly(.25*bep_flow), power_poly(.4*bep_flow), power_poly(.6*bep_flow), power_poly(.75*bep_flow), power_poly(.9*bep_flow), bep_power, power_poly(1.1*bep_flow), power_poly(1.2*bep_flow)])
        # calculator_spreadsheet_input_csv.extend([test2_flow_25, test2_flow_50, test2_flow_75])
        # calculator_spreadsheet_input_csv.extend([test2_head_25, test2_head_50, test2_head_75])
        # calculator_spreadsheet_input_csv.extend([test2_power_25, test2_power_50, test2_power_75])

        upload_spreadsheet_input_csv.extend(["Taco", "", test1name, test1name, "", "CP1", 109, "yes", "yes", "no", "no", "no", "no", "Pressure Control", "No speed control"])
        upload_spreadsheet_input_csv.extend([head_poly_reduced_string, head_poly_string])
        upload_spreadsheet_input_csv.extend([PEI_result["P_in_25"], PEI_result["P_in_50"], PEI_result["P_in_75"], PEI_result["P_in_100"]])
        upload_spreadsheet_input_csv.extend(["", ""])
        upload_spreadsheet_input_csv.extend([test1_power_25, test1_power_50, test1_power_75, bep_power])
        upload_spreadsheet_input_csv.extend(["", ""])
        upload_spreadsheet_input_csv.extend([test1_head_25, test1_head_50, test1_head_75, bep_head])
        upload_spreadsheet_input_csv.extend([bep_flow, PEI_result["PEI"], PEI_result["PEI_most_consumptive"]])

        doe_spreadsheet_input_csv.extend(["", "Taco", test1name, "CP1", "ECM", "", "", "", "", "", ""])
        doe_spreadsheet_input_csv.extend([bep_flow, bep_head, "", bep_power*745.699872, bep_flow*bep_head/(3960*bep_power)])
        doe_spreadsheet_input_csv.extend([flow_25, test1_head_25, "", test1_power_25*745.699872, flow_25*test1_head_25/(3960*test1_power_25)])
        doe_spreadsheet_input_csv.extend([flow_50, test1_head_50, "", test1_power_50*745.699872, flow_50*test1_head_50/(3960*test1_power_50)])
        doe_spreadsheet_input_csv.extend([flow_75, test1_head_75, "", test1_power_75*745.699872, flow_75*test1_head_75/(3960*test1_power_75)])
        doe_spreadsheet_input_csv.extend([flow_110, test1_head_110, "", test1_power_110*745.699872, flow_110*test1_head_110/(3960*test1_power_110)])
        doe_spreadsheet_input_csv.extend(["", "", "", "", ""])
        doe_spreadsheet_input_csv.extend([test2_flow_25, test2_head_25, "", test2_power_25*745.699872, test2_flow_25*test2_head_25/(3960*test2_power_25)])
        doe_spreadsheet_input_csv.extend([test2_flow_50, test2_head_50, "", test2_power_50*745.699872, test2_flow_50*test2_head_50/(3960*test2_power_50)])
        doe_spreadsheet_input_csv.extend([test2_flow_75, test2_head_75, "", test2_power_75*745.699872, test2_flow_75*test2_head_75/(3960*test2_power_75)])

    else:
        PEI_result = {
            "status": "failed",
            "PEI": 0,
            "ER": 0,
            "PEI_most_consumptive": 0,
            "ER_most_consumptive": 0,
        }
        calculator_spreadsheet_input_csv.extend([bep_flow, bep_head, power_poly(bep_flow)])
        calculator_spreadsheet_input_csv.extend([0.1*bep_flow, .25*bep_flow, .4*bep_flow, .6*bep_flow, .75*bep_flow, .9*bep_flow, bep_flow, 1.1*bep_flow, 1.2*bep_flow])
        calculator_spreadsheet_input_csv.extend([head_poly(0.1*bep_flow), head_poly(.25*bep_flow), head_poly(.4*bep_flow), head_poly(.6*bep_flow), head_poly(.75*bep_flow), head_poly(.9*bep_flow), bep_head, head_poly(1.1*bep_flow), head_poly(1.2*bep_flow)])
        calculator_spreadsheet_input_csv.extend([power_poly(0.1*bep_flow), power_poly(.25*bep_flow), power_poly(.4*bep_flow), power_poly(.6*bep_flow), power_poly(.75*bep_flow), power_poly(.9*bep_flow), bep_power, power_poly(1.1*bep_flow), power_poly(1.2*bep_flow)])
        calculator_spreadsheet_input_csv.extend([test2_flow_25, test2_flow_50, test2_flow_75])
        calculator_spreadsheet_input_csv.extend([test2_head_25, test2_head_50, test2_head_75])
        calculator_spreadsheet_input_csv.extend([test2_power_25, test2_power_50, test2_power_75])

        upload_spreadsheet_input_csv.extend(["Taco", "", test1name, test1name, "", "CP1", 109, "yes", "yes", "no", "no", "no", "no", "Pressure Control", "No speed control"])
        upload_spreadsheet_input_csv.extend([head_poly_reduced_string, head_poly_string])
        upload_spreadsheet_input_csv.extend([PEI_result["P_in_25"], PEI_result["P_in_50"], PEI_result["P_in_75"], PEI_result["P_in_100"]])
        upload_spreadsheet_input_csv.extend(["", ""])
        upload_spreadsheet_input_csv.extend([test1_power_25, test1_power_50, test1_power_75, bep_power])
        upload_spreadsheet_input_csv.extend(["", ""])
        upload_spreadsheet_input_csv.extend([test1_head_25, test1_head_50, test1_head_75, bep_head])
    
        doe_spreadsheet_input_csv.extend(["", "Taco", test1name, "CP1", "ECM", "", "", "", "", "", ""])
        doe_spreadsheet_input_csv.extend([bep_flow, bep_head, "", bep_power*745.699872, bep_flow*bep_head/(3960*bep_power)])
        doe_spreadsheet_input_csv.extend([flow_25, test1_head_25, "", test1_power_25*745.699872, flow_25*test1_head_25/(3960*test1_power_25)])
        doe_spreadsheet_input_csv.extend([flow_50, test1_head_50, "", test1_power_50*745.699872, flow_50*test1_head_50/(3960*test1_power_50)])
        doe_spreadsheet_input_csv.extend([flow_75, test1_head_75, "", test1_power_75*745.699872, flow_75*test1_head_75/(3960*test1_power_75)])
        doe_spreadsheet_input_csv.extend([flow_110, test1_head_110, "", test1_power_110*745.699872, flow_110*test1_head_110/(3960*test1_power_110)])
        doe_spreadsheet_input_csv.extend(["", "", "", "", ""])
        doe_spreadsheet_input_csv.extend([test2_flow_25, test2_head_25, "", test2_power_25*745.699872, test2_flow_25*test2_head_25/(3960*test2_power_25)])
        doe_spreadsheet_input_csv.extend([test2_flow_50, test2_head_50, "", test2_power_50*745.699872, test2_flow_50*test2_head_50/(3960*test2_power_50)])
        doe_spreadsheet_input_csv.extend([test2_flow_75, test2_head_75, "", test2_power_75*745.699872, test2_flow_75*test2_head_75/(3960*test2_power_75)])
    
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
        "calculator_csv_input": ",".join(map(str, calculator_spreadsheet_input_csv)),
        "upload_csv_input": ",".join(map(str, upload_spreadsheet_input_csv)),
        "doe_survey_csv_input": ",".join(map(str, doe_spreadsheet_input_csv)),
    }
    return JsonResponse(context)
