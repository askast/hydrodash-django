from django.http import HttpResponse
import numpy as np
import json

from django.db.models import F
from marketingdata.models import MarketingCurveDetail, MarketingCurveData
from pump.models import Pump, PumpTrim, NPSHData
from testdata.models import ReducedPumpTestDetails, ReducedPumpTestData
from pei.utils import calculatePEI

# Create your views here.
def getCoeffs(request):
    pump_str = [
        ["KV", "1506", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        [
            "KV",
            "1507",
            "D",
            [1160, 1450, 1760, 2900, 3500],
            [5.25, 5.75, 6.25, 6.75, 7.25],
        ],
        ["KV", "2006", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        [
            "KV",
            "2007",
            "D",
            [1160, 1450, 1760, 2900, 3500],
            [5.25, 5.75, 6.25, 6.75, 7.25],
        ],
        [
            "KV",
            "2009",
            "D",
            [1160, 1450, 1760, 2900, 3500],
            [6.75, 7.5, 8.25, 9.0, 9.5],
        ],
        ["KV", "3006", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        [
            "KV",
            "3007",
            "D",
            [1160, 1450, 1760, 2900, 3500],
            [5.5, 6.0, 6.5, 6.875, 7.25],
        ],
        [
            "KV",
            "3009",
            "D",
            [1160, 1450, 1760, 2900, 3500],
            [6.75, 7.5, 8.25, 9.0, 9.5],
        ],
        ["KV", "3013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        [
            "KV",
            "4007",
            "D",
            [1160, 1450, 1760, 2900, 3500],
            [5.25, 5.75, 6.25, 6.75, 7.25],
        ],
        [
            "KV",
            "4009",
            "D",
            [1160, 1450, 1760, 2900, 3500],
            [6.75, 7.5, 8.25, 9.0, 9.5],
        ],
        ["KV", "4011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        ["KV", "4013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        ["KV", "5007", "D", [1160, 1450, 1760, 2900, 3500], [5.75, 6.25, 6.75, 7.25]],
        ["KV", "6007", "D", [1160, 1450, 1760, 2900, 3500], [5.75, 6.25, 6.75, 7.25]],
        ["KV", "6009", "D", [1160, 1450, 1760], [7.0, 7.75, 8.5, 9.0, 9.5]],
        ["KV", "6011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        ["KV", "6013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        ["KV", "8011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        ["KV", "8013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
    ]

    return_string = ""
    return_list = []

    for series, model, d, speeds, trims in pump_str:
        for speed in speeds:
            return_object = {
                "Model": f"{series}{model}{d}",
                "Speed": speed,
                "#NPSH": 1,
                "#Trims": len(trims),
            }

            print(f"Looking up :\n {series}{model}{d} {speed}rpm")
            pumpobj = Pump.objects.get(
                series=series, pump_model=model, design_iteration=d, speed=speed
            )

            npsh_data = NPSHData.objects.filter(pump=pumpobj).values("flow", "npsh")
            npsh_data = np.array(
                [
                    [point["flow"] * 4.402862, point["npsh"] * 3.28084]
                    for point in npsh_data
                ]
            )
            npsh_data = npsh_data[np.argsort(npsh_data[:, 0])]
            return_object["NPSHMinFlow"] = [np.amin(npsh_data.T[0]).item(), 0]
            return_object["NPSHMaxFlow"] = [np.amax(npsh_data.T[0]).item(), 0]
            npsh_coeffs = list(np.polyfit(npsh_data.T[0], npsh_data.T[1], 3))
            npsh_coeffs.insert(0, 0)
            npsh_coeffs.insert(0, 0)
            return_object["NPSH-coeffs"] = npsh_coeffs
            head_coeffs_list = []
            eff_coeffs_list = []
            min_flows_list = []
            max_flows_list = []
            for trim in trims:
                print(f'Looking up :\n {trim}" trim')
                pump_trim_obj = PumpTrim.objects.get(
                    pump__series=series,
                    pump__pump_model=model,
                    pump__design_iteration=d,
                    pump__speed=speed,
                    trim=trim,
                )
                head_poly = np.poly1d(
                    getattr(pump_trim_obj.marketing_data, "headcoeffs")
                )
                eff_poly = np.poly1d(getattr(pump_trim_obj.marketing_data, "effcoeffs"))
                flows = list(
                    MarketingCurveData.objects.filter(
                        curveid=pump_trim_obj.marketing_data
                    )
                    .order_by("flow")
                    .values_list("flow", flat=True)
                )
                max_flow = flows[-1] * 4.402862
                sample_flows = np.linspace(0, max_flow, 30)
                sample_heads = head_poly(sample_flows)
                sample_effs = eff_poly(sample_flows) * 100

                head_coeffs = np.polyfit(sample_flows, sample_heads, 5).tolist()
                eff_coeffs = np.polyfit(sample_flows, sample_effs, 5).tolist()

                head_coeffs_list.append(head_coeffs)
                eff_coeffs_list.append(eff_coeffs)
                bep_flow = getattr(pump_trim_obj.marketing_data, "bep_flow")
                min_flows_list.append(0.3 * bep_flow * 4.402862)
                max_flows_list.append(max_flow)

            return_object["TrimMinFlows"] = min_flows_list
            return_object["TrimDia"] = trims
            return_object["TrimMaxFlows"] = max_flows_list
            return_object["Head-Coeff"] = head_coeffs_list
            return_object["Eff-Coeff"] = eff_coeffs_list
            return_list.append(return_object)

    return_string = json.dumps(return_list)

    return HttpResponse(return_string, content_type="text/plain")


def adjust4013(request):
    testids = [273, 272, 271]
    for testid in testids:
        testobj = ReducedPumpTestDetails.objects.get(id=testid)
        testdata = ReducedPumpTestData.objects.filter(testid=testobj)
        testdata.update(head=F("head") * 0.99)
    return HttpResponse("DID IT")


def flattenInflection(request):
    flatten_inflection_list = [["KV", "2009", 1450, 20]]
    for series, model, speed, percent in flatten_inflection_list:
        market_curves = PumpTrim.objects.filter(
            pump__series=series, pump__pump_model=model, pump__speed=speed
        ).values("marketing_data")
        for curve in market_curves:
            print(f'curve:{curve["marketing_data"]}')
            curve = MarketingCurveDetail.objects.get(id=curve["marketing_data"])
            bep_flow = getattr(curve, "bep_flow")
            print(f"curve:{curve}")
            curvedataqs = MarketingCurveData.objects.filter(curveid=curve).order_by(
                "-flow"
            )
            flat_head = 0
            flow = []
            head = []
            for datapoint in curvedataqs:
                print(f"datapointflow:{datapoint.flow}, 15% bep_flow:{bep_flow *.15}")
                flow.append(datapoint.flow)
                head.append(datapoint.head)
                if datapoint.flow < percent * bep_flow / 100:
                    if flat_head == 0:
                        flat_head = datapoint.head
                    else:
                        print(f"before:{datapoint.head}")
                        datapoint.head = flat_head
                        datapoint.save()
                        print(f"after:{datapoint.head}")
            flow = np.array(flow)
            head = np.array(head)
            headcoeffs = list(np.polyfit(flow / 0.227125, head / 0.3048, 5))
            curve.headcoeffs = headcoeffs
            curve.save()

    return HttpResponse(f"Flattened: {flatten_inflection_list}")


def copyKS(request):
    ks_list = ["4007"]
    for model in ks_list:
        kv_pumps = PumpTrim.objects.filter(pump__series="KV", pump__pump_model=model)
        for pump in kv_pumps:
            # pumpid = Pump.objects.get(id=pump.pump)
            design = getattr(pump.pump, "design_iteration")
            speed = getattr(pump.pump, "speed")
            eng = pump.engineering_data
            trim = pump.trim
            mark = pump.marketing_data
            print(f"model:{model}")
            ks_pump = PumpTrim.objects.get(
                pump__series="KS",
                pump__pump_model=model,
                pump__design_iteration=design,
                pump__speed=speed,
                trim=trim,
            )
            ks_pump.engineering_data = eng
            ks_pump.marketing_data = mark
            ks_pump.save()
    for model in ks_list:
        NPSH_data_lines = NPSHData.objects.filter(
            pump__series="KV", pump__pump_model=model
        )

        NPSHData.objects.filter(pump__series="KS", pump__pump_model=model).delete()
        for npsh in NPSH_data_lines:
            # pumpid = Pump.objects.get(id=pump.pump)
            design = getattr(npsh.pump, "design_iteration")
            speed = getattr(npsh.pump, "speed")
            flow = npsh.flow
            npsh_head = npsh.npsh
            print(f"model:{model}")
            ks_pump = Pump.objects.get(
                series="KS", pump_model=model, design_iteration=design, speed=speed
            )
            ks_npsh_line = NPSHData(pump=ks_pump, flow=flow, npsh=npsh_head)
            ks_npsh_line.save()

    return HttpResponse(f"KS copied: {ks_list}")


def getPEIupload(request):
    # Manufacturer, Brand, Basic Model, model number, Equipment Category, Configuration, Full trim, 3, 1, Nominal Speed, , yes, Motor Efficiency,
    # Motor horsepower, yes, 100% BEP Flow, 75% BEP Flow, 110% BEP Flow, , , 100% BEP Head,  ,  , , , Driver Input Power @ 100% , Driver Input Power @ 75% ,
    # Driver Input Power @ 110%, , , Control power input at 25%, Control power input at 50%, Control power input at 75%, Control power input at 100%,
    # PEI, Head at 75%, Head at 110%, Head at 65%, Head at 90%, 109,
    pump_str = [
        ["KV", "1506", "D", [1760, 3500], 6.25],
        ["KV", "1507", "D", [1760, 3500], 7.25],
        ["KV", "2006", "D", [1760, 3500], 6.25],
        ["KV", "2007", "D", [1760, 3500], 7.25],
        ["KV", "2009", "D", [1760, 3500], 9.5],
        ["KV", "3006", "D", [1760, 3500], 6.25],
        ["KV", "3007", "D", [1760, 3500], 7.25],
        ["KV", "4007", "D", [1760, 3500], 7.25],
        ["KV", "5007", "D", [1760, 3500], 7.25],
        ["KV", "6009", "D", [1760], 9.5],
    ]
    return_string = ""
    for series, model, d, speeds, trim in pump_str:
        for speed in speeds:
            print(f"Looking up :\n {series}{model}{d} {speed}rpm")
            pump_trim_obj = PumpTrim.objects.get(
                    pump__series=series,
                    pump__pump_model=model,
                    pump__design_iteration=d,
                    pump__speed=speed,
                    trim=trim,
                )
            flows = list(
                    MarketingCurveData.objects.filter(
                        curveid=pump_trim_obj.marketing_data
                    )
                    .order_by("flow")
                    .values_list("flow", flat=True)
                )
            heads = list(
                    MarketingCurveData.objects.filter(
                        curveid=pump_trim_obj.marketing_data
                    )
                    .order_by("flow")
                    .values_list("head", flat=True)
                )
            powers = list(
                    MarketingCurveData.objects.filter(
                        curveid=pump_trim_obj.marketing_data
                    )
                    .order_by("flow")
                    .values_list("power", flat=True)
                )
            bep_flow = getattr(pump_trim_obj.marketing_data, "bep_flow")
            flow_75 = 0.75 * bep_flow 
            flow_110 = 1.1 * bep_flow
            flow_120 = 1.2 * bep_flow

            headpoly = np.poly1d(np.polyfit(flows, heads, 6))
            powerpoly = np.poly1d(np.polyfit(flows, powers, 6))

            bep_head = headpoly(bep_flow)
            head_75 = headpoly(flow_75)
            head_110 = headpoly(flow_110)

            bep_power = powerpoly(bep_flow)
            power_75 = powerpoly(flow_75)
            power_110 = powerpoly(flow_110)
            power_120 = powerpoly(flow_120)
            
            if series == "FI":
                category = "ESCC"
            elif series == "CI":
                category = "ESFM"
            else:
                category = "IL"


            if speed == 1760:
                nomspeed = 1800
                modelnumber = f'{series}{model}D-4P-PM'
            else:
                nomspeed = 3600
                modelnumber = f'{series}{model}D-2P-PM'

            pei = calculatePEI(bep_flow, bep_head,
                bep_power,
                flow_75,
                head_75,
                power_75,
                flow_110,
                head_110,
                power_110,
                power_120,
                speed,
                category,
                "BP",
                motor_hp=0,
                motor_eff=0,
            )
            """
            return {
                "status": "success",
                "PEIcl": PEIcl,
                "PEIvl": PEIvl,
                "flow_bep": bep_flow_corr,
                "head_75": head_75_corr,
                "head_bep": bep_head_corr,
                "head_110": head_110_corr,
                "power_75": power_75_corr,
                "power_bep": bep_power_corr,
                "power_110": power_110_corr,
                "controller_power_25": drive_input_power_25,
                "controller_power_50": drive_input_power_50,
                "controller_power_75": drive_input_power_75,
                "controller_power_bep": drive_input_power_bep,
                "motor_hp": motor_hp,
                "motor_eff": motor_eff,
            }
            """

            return_string += f"Taco, Taco, {series}{model}, {modelnumber}, {category}, Bare pump + motor, {trim}, 4, 1, {nomspeed}, , yes, {pei['motor_eff']}, \
{pei['motor_hp']}, yes, {pei['flow_bep']}, {pei['flow_bep']*0.75}, {pei['flow_bep']*1.1}, , , {pei['head_bep']}, , , , , {pei['power_bep']}, {pei['power_75']}, \
{pei['power_110']}, , , , , , , {pei['PEIcl']}, {pei['head_75']}, {pei['head_110']}, , , 109,\n"
            return_string += f"Taco, Taco, S{series}{model}, {modelnumber[:-2]}PD, {category}, Bare pump + motor + continuous control, {trim}, 6, 1, {nomspeed}, , yes, {pei['motor_eff']}, \
{pei['motor_hp']}, yes, {pei['flow_bep']}, {pei['flow_bep']*0.75}, {pei['flow_bep']*1.1}, , , {pei['head_bep']}, , , , , , , , , , {pei['controller_power_25']}, \
{pei['controller_power_50']}, {pei['controller_power_75']}, {pei['controller_power_bep']}, {pei['PEIvl']}, {pei['head_75']}, {pei['head_110']}, , , 109,\n"
    
    return HttpResponse(return_string, content_type="text/plain")


def populatePumps(request):
    curvenumbers_string = """
KS	6009	D	1760	PC	4329
KS	6009	D	1450	PC	4330
KS	6009	D	1160	PC	4331
KS	2009	D	3500	PC	4313
KS	2009	D	1760	PC	4315
KS	2009	D	2900	PC	4314
KS	2009	D	1450	PC	4316
KS	2009	D	1160	PC	4317
"""
    for line in curvenumbers_string.strip().split("\n"):
        series, pumpmodel, design, speed, pc, curve_number = line.split("\t")
        print(
            f"series:{series}; pumpmodel:{pumpmodel}; design:{design}; speed:{speed}; curvenumber:{curve_number}"
        )
        pumpObj = Pump.objects.filter(
            series=series.strip(),
            pump_model=pumpmodel.strip(),
            design_iteration=design.strip(),
            speed=speed.strip(),
        )
        print(pumpObj)
        pumpObj.update(
            curve_number=curve_number.strip(),
            curve_rev=f"{pc.strip()}-{curve_number.strip()} Rev -",
        )
    return HttpResponse(f'updated: \n{curvenumbers_string}', content_type="text/plain")
    # fi_pumps = Pump.objects.filter(series="CI")
    # for pump in fi_pumps:
    #     rev = pump.curve_rev
    #     print(f'model:{pump.pump_model}')
    #     print(f'rev:{rev}')
    #     if '-' in rev:
    #         deconstructed_rev = rev.split('-')
    #         new_rev = f'PC-{deconstructed_rev[1]} Rev A'
    #         pump.curve_rev = new_rev
    #         pump.save()