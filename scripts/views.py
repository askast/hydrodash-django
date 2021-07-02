from django.http import HttpResponse
import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta

from django.db.models import F
from marketingdata.models import MarketingCurveDetail, MarketingCurveData
from pump.models import Pump, PumpTrim, NPSHData
from testdata.models import ReducedPumpTestDetails, ReducedPumpTestData, RawTestsList
from pei.utils import calculatePEI
from pump.models import OldTestDetails

# Create your views here.
def getCoeffs(request):
    pump_str = [
        # ["KV", "1506", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["KV", "1507", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["KV", "2006", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["KV", "2007", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["KV", "2009", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25, 9.0, 9.5]],
        # ["KV", "3006", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["KV", "3007", "D", [1160, 1450, 1760, 2900, 3500], [5.5, 6.0, 6.5, 6.875, 7.25]],
        # ["KV", "3009", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25, 9.0, 9.5]],
        # ["KV", "3011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["KV", "3013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["KV", "4007", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["KV", "4009", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25, 9.0, 9.5]],
        # ["KV", "4011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["KV", "4013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["KV", "5007", "D", [1160, 1450, 1760, 2900, 3500], [5.75, 6.25, 6.75, 7.25]],
        # ["KV", "6007", "D", [1160, 1450, 1760, 2900, 3500], [5.75, 6.25, 6.75, 7.25]],
        # ["KV", "6009", "D", [1160, 1450, 1760], [7.0, 7.75, 8.5, 9.0, 9.5]],
        # ["KV", "6011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["KV", "6013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["KV", "8011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["KV", "8013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["KV", "8013", "D", [1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["KS", "1506", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["KS", "1507", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["KS", "2006", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["KS", "2007", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["KS", "2009", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25, 9.0, 9.5]],
        # ["KS", "3006", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["KS", "3007", "D", [1160, 1450, 1760, 2900, 3500], [5.5, 6.0, 6.5, 6.875, 7.25]],
        # ["KS", "3009", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25, 9.0, 9.5]],
        # ["KS", "3011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["KS", "3013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["KS", "4007", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["KS", "4009", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25, 9.0, 9.5]],
        # ["KS", "4011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["KS", "4013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["KS", "5007", "D", [1160, 1450, 1760, 2900, 3500], [5.75, 6.25, 6.75, 7.25]],
        ["KS", "6007", "D", [1160, 1450, 1760, 2900, 3500], [5.75, 6.25, 6.75, 7.25]],
        # ["KS", "6009", "D", [1160, 1450, 1760], [7.0, 7.75, 8.5, 9.0, 9.5]],
        # ["KS", "6011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["KS", "6013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["KS", "8011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["KS", "8013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["FI", "1206", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["FI", "1506", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["FI", "2506", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["FI", "1207", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["FI", "1507", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["FI", "2007", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["FI", "2007", "D", [3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["FI", "2507", "D", [1160, 1450, 1760, 2900, 3500], [5.5, 6.0, 6.5, 6.875, 7.25]],
        # ["FI", "3007", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["FI", "4007", "D", [1160, 1450, 1760, 2900, 3500], [5.75, 6.25, 6.75, 7.25]],
        # ["FI", "5007", "D", [1160, 1450, 1760, 2900, 3500], [5.75, 6.25, 6.75, 7.25]],
        # ["FI", "1509", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25, 9.0, 9.5]],
        # ["FI", "2009", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25, 9.0, 9.5]],
        # ["FI", "2509", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25,  9.0, 9.5]],
        # ["FI", "3009", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25,  9.0, 9.5]],
        # ["FI", "4009", "D", [1160, 1450, 1760], [6.75, 7.5, 8.25,  9.0, 9.5]],
        # ["FI", "4009", "D", [1760], [6.75, 7.5, 8.25,  9.0, 9.5]],
        # ["FI", "5009", "D", [1160, 1450, 1760], [7.0, 7.5, 8.0, 8.5, 9.0, 9.5]],
        # ["FI", "6009", "D", [1160, 1450, 1760], [7.5, 8.0, 8.5, 9.0, 9.5]],
        # ["FI", "2511", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["FI", "3011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["FI", "5011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["FI", "6011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["FI", "2513", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["FI", "3013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["FI", "4013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["FI", "5013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["FI", "6013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["FI", "8013", "D", [1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["FI", "8013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["CI", "1206", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["CI", "1506", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["CI", "2506", "D", [1450, 1760, 2900, 3500], [4.25, 4.75, 5.25, 5.75, 6.25]],
        # ["CI", "1207", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["CI", "1507", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["CI", "2007", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["CI", "2007", "D", [3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["CI", "2507", "D", [1160, 1450, 1760, 2900, 3500], [5.5, 6.0, 6.5, 6.875, 7.25]],
        # ["CI", "3007", "D", [1160, 1450, 1760, 2900, 3500], [5.25, 5.75, 6.25, 6.75, 7.25]],
        # ["CI", "4007", "D", [1160, 1450, 1760, 2900, 3500], [5.75, 6.25, 6.75, 7.25]],
        # ["CI", "5007", "D", [1160, 1450, 1760, 2900, 3500], [5.75, 6.25, 6.75, 7.25]],
        # ["CI", "1509", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25, 9.0, 9.5]],
        # ["CI", "2009", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25, 9.0, 9.5]],
        # ["CI", "2509", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25,  9.0, 9.5]],
        # ["CI", "3009", "D", [1160, 1450, 1760, 2900, 3500], [6.75, 7.5, 8.25,  9.0, 9.5]],
        # ["CI", "4009", "D", [1160, 1450, 1760], [6.75, 7.5, 8.25,  9.0, 9.5]],
        # ["CI", "5009", "D", [1160, 1450, 1760], [7.0, 7.5, 8.0, 8.5, 9.0, 9.5]],
        # ["CI", "6009", "D", [1160, 1450, 1760], [7.5, 8.0, 8.5, 9.0, 9.5]],
        # ["CI", "2511", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["CI", "3011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["CI", "5011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["CI", "6011", "D", [1160, 1450, 1760], [8.0, 8.75, 9.5, 10.25, 11.0]],
        # ["CI", "2513", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["CI", "3013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
        # ["CI", "4013", "D", [1160, 1450, 1760], [9.5, 10.5, 11.5, 12.5, 13.5]],
    ]

    return_string = "Pump, Speed, Diameter, Flow, Head, Flow, Eta, NPSH Flow, NPSH"
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
            npsh_poly = np.poly1d(np.polyfit(npsh_data.T[0], npsh_data.T[1], 3))
            npsh_coeffs.insert(0, 0)
            npsh_coeffs.insert(0, 0)
            
            sample_npsh_flows = np.linspace(np.amin(npsh_data.T[0]).item(), np.amax(npsh_data.T[0]).item(), 30)
            sample_npsh = npsh_poly(sample_npsh_flows)

            return_object["NPSH-coeffs"] = npsh_coeffs
            head_coeffs_list = []
            eff_coeffs_list = []
            min_flows_list = []
            max_flows_list = []
            sample_flows_list = []
            sample_heads_list = []
            sample_effs_list = []
            max_trim = max(trims)

            # get max flow of max trim
            pump_max_trim_obj = PumpTrim.objects.get(
                pump__series=series,
                pump__pump_model=model,
                pump__design_iteration=d,
                pump__speed=speed,
                trim=max_trim,
            )
            head_poly_max = np.poly1d(
                getattr(pump_max_trim_obj.marketing_data, "headcoeffs")
            )
            # eff_poly_max = np.poly1d(getattr(pump_max_trim_obj.marketing_data, "effcoeffs"))
            flows_max = list(
                MarketingCurveData.objects.filter(
                    curveid=pump_max_trim_obj.marketing_data
                )
                .order_by("flow")
                .values_list("flow", flat=True)
            )
            max_flow = flows_max[-1] * 4.402862

            # establish quadratic of max flows
            a_max = head_poly_max(max_flow).item() / pow(max_flow, 2)
            

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

                # determine max flow as intersection of quadratic and head_poly
                if trim != max_trim:
                    temp_flows = np.linspace(0, (max_flow + 5), 100)
                    curve_heads = head_poly(temp_flows)
                    temp_heads = np.power(temp_flows, 2) * a_max
                    # print(f"curve:{curve_heads}\ntemp:{temp_heads}")
                    intercept_flowheads_max = interpolated_intercept(temp_flows, temp_heads, curve_heads)
                    trim_max_flow = intercept_flowheads_max[0]
                else:
                    trim_max_flow = max_flow

                sample_flows = np.linspace(0, trim_max_flow, 30)
                sample_heads = head_poly(sample_flows)
                sample_effs = eff_poly(sample_flows) * 100
                # sample_flows_list.append(sample_flows)
                # sample_heads_list.append(sample_heads)
                # sample_effs_list.append(sample_effs)
                for sflow, shead, seff, snflow, snpsh in zip(sample_flows, sample_heads, sample_effs, sample_npsh_flows, sample_npsh):
                    if trim == max_trim:
                        return_string += f"\n{series}{model}{d}, {speed}, {trim}, {sflow}, {shead}, {sflow}, {seff}, {snflow}, {snpsh}"
                    else:
                        return_string += f"\n{series}{model}{d}, {speed}, {trim}, {sflow}, {shead}, {sflow}, {seff}, , "
                head_coeffs = np.polyfit(sample_flows, sample_heads, 5).tolist()
                eff_coeffs = np.polyfit(sample_flows, sample_effs, 5).tolist()

                head_coeffs_list.append(head_coeffs)
                eff_coeffs_list.append(eff_coeffs)
                bep_flow = getattr(pump_trim_obj.marketing_data, "bep_flow")
                min_flows_list.append(0.3 * bep_flow * 4.402862)
                max_flows_list.append(trim_max_flow)

            return_object["TrimMinFlows"] = min_flows_list
            return_object["TrimDia"] = trims
            return_object["TrimMaxFlows"] = max_flows_list
            return_object["Head-Coeff"] = head_coeffs_list
            return_object["Eff-Coeff"] = eff_coeffs_list
            return_list.append(return_object)

            

    # return_string = json.dumps(return_list)
        
     
    response = HttpResponse(return_string, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename={0}'.format("Intelliquip_export.csv")
    return response

    # return HttpResponse(return_string, content_type="text/plain")

def interpolated_intercept(x, y1, y2):
    """Find the intercept of two curves, given by the same x data"""
    # print(f'x: {x}\ny1: {y1}\ny2: {y2}')

    def intercept(point1, point2, point3, point4):
        """find the intersection between two lines
        the first line is defined by the line between point1 and point2
        the first line is defined by the line between point3 and point4
        each point is an (x,y) tuple.

        So, for example, you can find the intersection between
        intercept((0,0), (1,1), (0,1), (1,0)) = (0.5, 0.5)

        Returns: the intercept, in (x,y) format
        """

        def line(p1, p2):
            A = p1[1] - p2[1]
            B = p2[0] - p1[0]
            C = p1[0] * p2[1] - p2[0] * p1[1]
            return A, B, -C

        def intersection(L1, L2):
            D = L1[0] * L2[1] - L1[1] * L2[0]
            Dx = L1[2] * L2[1] - L1[1] * L2[2]
            Dy = L1[0] * L2[2] - L1[2] * L2[0]

            x = Dx / D
            y = Dy / D
            return x, y

        L1 = line([point1[0], point1[1]], [point2[0], point2[1]])
        L2 = line([point3[0], point3[1]], [point4[0], point4[1]])

        R = intersection(L1, L2)

        return R

    idx = np.argwhere(np.diff(np.sign(y1 - y2)) != 0)
    xc, yc = intercept(
        (x[idx], y1[idx]),
        ((x[idx + 1], y1[idx + 1])),
        ((x[idx], y2[idx])),
        ((x[idx + 1], y2[idx + 1])),
    )
    # print(f'xc:{xc}')
    # print(f'yc:{yc}')
    return xc.item(0), yc.item(0)


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
    ks_list = ["1509", "2011"]
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
            # ks_pump = PumpTrim.objects.get(
            #     pump__series="KS",
            #     pump__pump_model=model,
            #     pump__design_iteration=design,
            #     pump__speed=speed,
            #     trim=trim,
            # )
            # ks_pump.engineering_data = eng
            # ks_pump.marketing_data = mark
            # ks_pump.save()
    # for model in ks_list:
    #     NPSH_data_lines = NPSHData.objects.filter(
    #         pump__series="CI", pump__pump_model=model
    #     )

    #     NPSHData.objects.filter(pump__series="FI", pump__pump_model=model).delete()
    #     for npsh in NPSH_data_lines:
    #         # pumpid = Pump.objects.get(id=pump.pump)
    #         design = getattr(npsh.pump, "design_iteration")
    #         speed = getattr(npsh.pump, "speed")
    #         flow = npsh.flow
    #         npsh_head = npsh.npsh
    #         print(f"model:{model}")
    #         ks_pump = Pump.objects.get(
    #             series="FI", pump_model=model, design_iteration=design, speed=speed
    #         )
    #         ks_npsh_line = NPSHData(pump=ks_pump, flow=flow, npsh=npsh_head)
    #         ks_npsh_line.save()

    return HttpResponse(f"KS copied: {ks_list}")


def getPEIupload(request):
    # Manufacturer, Brand, Basic Model, model number, Equipment Category, Configuration, Full trim, 3, 1, Nominal Speed, , yes, Motor Efficiency,
    # Motor horsepower, yes, 100% BEP Flow, 75% BEP Flow, 110% BEP Flow, , , 100% BEP Head,  ,  , , , Driver Input Power @ 100% , Driver Input Power @ 75% ,
    # Driver Input Power @ 110%, , , Control power input at 25%, Control power input at 50%, Control power input at 75%, Control power input at 100%,
    # PEI, Head at 75%, Head at 110%, Head at 65%, Head at 90%, 109,
    pump_str = [
        # ["FI", "1206", "D", [1760, 3500], 6.25],
        # ["FI", "1506", "D", [1760, 3500], 6.25],
        # ["FI", "2506", "D", [1760, 3500], 6.25],
        # ["FI", "1207", "D", [1760, 3500], 7.25],
        # ["FI", "1507", "D", [1760, 3500], 7.25],
        # ["FI", "2007", "D", [1760, 3500], 7.25],
        # ["FI", "2507", "D", [1760, 3500], 7.25],
        # ["FI", "3007", "D", [1760, 3500], 7.25],
        # ["FI", "4007", "D", [1760, 3500], 7.25],
        # ["FI", "5007", "D", [1760, 3500], 7.25],
        # ["FI", "1509", "D", [1760, 3500], 9.5],
        # ["FI", "2009", "D", [1760, 3500], 9.5],
        # ["FI", "2509", "D", [1760, 3500], 9.5],
        # ["FI", "3009", "D", [1760, 3500], 9.5],
        # ["FI", "4009", "D", [1760], 9.5],
        # ["FI", "5009", "D", [1760], 9.5],
        # ["FI", "6009", "D", [1760], 9.5],
        # ["FI", "2511", "D", [1760], 11.0],
        # ["FI", "3011", "D", [1760], 11.0],
        # ["FI", "5011", "D", [1760], 11.0],
        # ["FI", "6011", "D", [1760], 11.0],
        # ["FI", "2513", "D", [1760], 13.5],
        # ["FI", "3013", "D", [1760], 13.5],
        # ["FI", "4013", "D", [1760], 13.5],
        # ["FI", "5013", "D", [1760], 13.5],
        # ["FI", "6013", "D", [1760], 13.5],
        # ["FI", "8013", "D", [1760], 13.5],
        # ["CI", "1206", "D", [1760, 3500], 6.25],
        # ["CI", "1506", "D", [1760, 3500], 6.25],
        # ["CI", "2506", "D", [1760, 3500], 6.25],
        # ["CI", "1207", "D", [1760, 3500], 7.25],
        # ["CI", "1507", "D", [1760, 3500], 7.25],
        # ["CI", "2007", "D", [1760, 3500], 7.25],
        # ["CI", "2507", "D", [1760, 3500], 7.25],
        # ["CI", "3007", "D", [1760, 3500], 7.25],
        # ["CI", "4007", "D", [1760, 3500], 7.25],
        # ["CI", "5007", "D", [1760, 3500], 7.25],
        # ["CI", "1509", "D", [1760, 3500], 9.5],
        # ["CI", "2009", "D", [1760, 3500], 9.5],
        # ["CI", "2509", "D", [1760, 3500], 9.5],
        # ["CI", "3009", "D", [1760, 3500], 9.5],
        # ["CI", "4009", "D", [1760], 9.5],
        # ["CI", "5009", "D", [1760], 9.5],
        # ["CI", "6009", "D", [1760], 9.5],
        # ["CI", "2511", "D", [1760], 11.0],
        # ["CI", "3011", "D", [1760], 11.0],
        # ["CI", "5011", "D", [1760], 11.0],
        # ["CI", "6011", "D", [1760], 11.0],
        # ["CI", "2513", "D", [1760], 13.5],
        # ["CI", "3013", "D", [1760], 13.5],
        # ["CI", "4013", "D", [1760], 13.5],
        # ["KV", "6007", "D", [1760, 3500], 7.25],
        # ["KV", "3009", "D", [1760, 3500], 9.5],
        # ["KV", "3011", "D", [1760], 11.0],
        # ["KV", "3013", "D", [1760], 13.5],
        # ["KV", "4009", "D", [1760, 3500], 9.5],
        # ["KV", "4011", "D", [1760], 11.0],
        # ["KV", "4013", "D", [1760], 13.5],
        # ["KV", "6007", "D", [1760, 3500], 7.25],
        # ["KV", "6011", "D", [1760], 11.0],
        # ["KV", "6013", "D", [1760], 13.5],
        # ["KV", "8011", "D", [1760], 11.0],
        # ["KV", "8013", "D", [1760], 13.5],
        # ["KV", "1509", "C", [1760, 3500], 9.5],
        # ["KV", "2011", "C", [1760], 11.25],
        # ["KS", "3009", "D", [1760, 3500], 9.5],
        # ["KS", "3011", "D", [1760], 11.0],
        # ["KS", "3013", "D", [1760], 13.5],
        # ["KS", "4009", "D", [1760, 3500], 9.5],
        # ["KS", "4011", "D", [1760], 11.0],
        # ["KS", "4013", "D", [1760], 13.5],
        # ["KS", "6007", "D", [1760, 3500], 7.25],
        # ["KS", "6011", "D", [1760], 11.0],
        # ["KS", "6013", "D", [1760], 13.5],
        # ["KS", "8011", "D", [1760], 11.0],
        # ["KS", "8013", "D", [1760], 13.5],
        # ["KS", "1509", "C", [1760, 3500], 9.5],
        # ["KS", "2011", "C", [1760], 11.25],
        # ["KS", "8016", "C", [1760], 16.5],
        # ["KS", "1013", "C", [1760], 13.0],
        # ["1600", "1611", "C", [1760, 3500], 4.75],
        # ["1600", "1615", "C", [1760], 6.35],
        # ["1600", "1615", "C", [3500], 6.25],
        # ["1600", "1619", "C", [1760], 7.9],
        # ["1600", "1635", "C", [1760], 6.15],
        # ["1600", "1635", "C", [3500], 5.75],
        # ["1600", "1641", "C", [1760], 7.9],
        # ["FI", "1209", "B", [1760], 9.5],
        # ["FI", "1209", "B", [3500], 9.5],
        # ["FI", "1511", "B", [1760], 11.0],
        # ["FI", "2510", "C", [1760], 10.0],
        # ["FI", "1206", "B", [1760, 3500], 6.25],
        # ["FI", "1506", "B", [1760, 3500], 6.25],
        # ["FI", "1207", "B", [1760, 3500], 7.5],
        # ["FI", "2007", "A", [1760, 3500], 7.25],
        # ["FI", "4007", "A", [1760, 3500], 7.5],
        # ["FI", "5007", "A", [1760, 3500], 7.15],
        # ["FI", "2509", "C", [1760, 3500], 9.5],
        # ["FI", "3009", "C", [1760, 3500], 9.25],
        # ["FI", "5009", "C", [1760], 9.25],
        # ["FI", "6009", "B", [1760], 9.5],
        # ["FI", "2511", "A", [1760], 11.25],
        # ["FI", "3011", "A", [1760], 11.25],
        # ["FI", "5011", "A", [1760], 11.25],
        # ["FI", "6011", "A", [1760], 11.25],
        # ["FI", "2513", "A", [1760], 13.0],
        # ["FI", "3013", "A", [1760], 13.0],
        # ["FI", "4013", "A", [1760], 12.75],
        # ["FI", "5013", "A", [1760], 13.0],
        # ["FI", "6013", "A", [1760], 13.0],
        # ["FI", "8013", "A", [1760], 13.25],
        # ["FI", "1509", "C", [1760, 3500], 9.25],
        # ["FI", "2009", "C", [1760, 3500], 9.5],
        # ["FI", "4009", "C", [1760], 9.25],
        # ["FI", "1507", "B", [1760, 3500], 7.5],
        # ["KV", "6011", "A", [1760], 11.25],
        # ["KV", "1506", "A", [1760, 3500], 6.25],
        # ["KV", "3009", "A", [1760, 3500], 9.25],
        # ["KV", "4009", "A", [1760, 3500], 9.25],
        # ["KV", "4011", "A", [1760], 11.25],
        # ["KV", "6011", "A", [1760], 11.25],
        # ["KV", "8011", "A", [1760], 11.25],
        # ["KV", "6013", "A", [1760], 13.0],
        # ["KV", "2510", "A", [1760], 10.25],
        # ["KV", "2006", "A", [1760, 3500], 6.25],
        # ["KV", "1507", "A", [1760, 3500], 7.5],
        # ["KV", "2007", "A", [1760, 3500], 7.5],
        # ["KV", "3007", "A", [1760, 3500], 7.5],
        # ["KV", "2009", "A", [1760, 3500], 9.25],
        # ["KV", "6009", "A", [1760], 9.25],
        # ["KV", "3011", "A", [1760], 11.25],
        # ["KV", "4013", "A", [1760], 13.0],
        # ["KV", "8013", "A", [1760], 13.0],
        ["FI", "1207", "D", [1160], 7.25],
        ["FI", "1507", "D", [1160], 7.25],
        ["FI", "2007", "D", [1160], 7.25],
        ["FI", "2507", "D", [1160], 7.25],
        ["FI", "3007", "D", [1160], 7.25],
        ["FI", "4007", "D", [1160], 7.25],
        ["FI", "5007", "D", [1160], 7.25],
        ["FI", "1509", "D", [1160], 9.5],
        ["FI", "2009", "D", [1160], 9.5],
        ["FI", "2509", "D", [1160], 9.5],
        ["FI", "3009", "D", [1160], 9.5],
        ["FI", "4009", "D", [1160], 9.5],
        ["FI", "5009", "D", [1160], 9.5],
        ["FI", "6009", "D", [1160], 9.5],
        ["FI", "2511", "D", [1160], 11.0],
        ["FI", "3011", "D", [1160], 11.0],
        ["FI", "5011", "D", [1160], 11.0],
        ["FI", "6011", "D", [1160], 11.0],
        ["FI", "2513", "D", [1160], 13.5],
        ["FI", "3013", "D", [1160], 13.5],
        ["FI", "4013", "D", [1160], 13.5],
        ["FI", "5013", "D", [1160], 13.5],
        ["FI", "6013", "D", [1160], 13.5],
        ["FI", "8013", "D", [1160], 13.5],
        ["CI", "1207", "D", [1160], 7.25],
        ["CI", "1507", "D", [1160], 7.25],
        ["CI", "2007", "D", [1160], 7.25],
        ["CI", "2507", "D", [1160], 7.25],
        ["CI", "3007", "D", [1160], 7.25],
        ["CI", "4007", "D", [1160], 7.25],
        ["CI", "5007", "D", [1160], 7.25],
        ["CI", "1509", "D", [1160], 9.5],
        ["CI", "2009", "D", [1160], 9.5],
        ["CI", "2509", "D", [1160], 9.5],
        ["CI", "3009", "D", [1160], 9.5],
        ["CI", "4009", "D", [1160], 9.5],
        ["CI", "5009", "D", [1160], 9.5],
        ["CI", "6009", "D", [1160], 9.5],
        ["CI", "2511", "D", [1160], 11.0],
        ["CI", "3011", "D", [1160], 11.0],
        ["CI", "5011", "D", [1160], 11.0],
        ["CI", "6011", "D", [1160], 11.0],
        ["CI", "2513", "D", [1160], 13.5],
        ["CI", "3013", "D", [1160], 13.5],
        ["CI", "4013", "D", [1160], 13.5],
        ["KV", "6007", "D", [1160], 7.25],
        ["KV", "3009", "D", [1160], 9.5],
        ["KV", "3011", "D", [1160], 11.0],
        ["KV", "3013", "D", [1160], 13.5],
        ["KV", "4009", "D", [1160], 9.5],
        ["KV", "4011", "D", [1160], 11.0],
        ["KV", "4013", "D", [1160], 13.5],
        ["KV", "6007", "D", [1160], 7.25],
        ["KV", "6011", "D", [1160], 11.0],
        ["KV", "6013", "D", [1160], 13.5],
        ["KV", "8011", "D", [1160], 11.0],
        ["KV", "8013", "D", [1160], 13.5],
        ["KV", "1509", "C", [1160], 9.5],
        ["KV", "2011", "C", [1160], 11.25],
        ["KS", "3009", "D", [1160], 9.5],
        ["KS", "3011", "D", [1160], 11.0],
        ["KS", "3013", "D", [1160], 13.5],
        ["KS", "4009", "D", [1160], 9.5],
        ["KS", "4011", "D", [1160], 11.0],
        ["KS", "4013", "D", [1160], 13.5],
        ["KS", "6007", "D", [1160], 7.25],
        ["KS", "6011", "D", [1160], 11.0],
        ["KS", "6013", "D", [1160], 13.5],
        ["KS", "8011", "D", [1160], 11.0],
        ["KS", "8013", "D", [1160], 13.5],
        ["KS", "1509", "C", [1160], 9.5],
        ["KS", "2011", "C", [1160], 11.25],
        # ["KS", "8016", "C", [1160], 16.5],
        # ["KS", "1013", "C", [1160], 13.0],
        # ["1600", "1611", "C", [1160], 4.75],
        # ["1600", "1615", "C", [1160], 6.35],
        # ["1600", "1619", "C", [1160], 7.9],
        # ["1600", "1635", "C", [1160], 6.15],
        # ["1600", "1641", "C", [1160], 7.9],
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
                MarketingCurveData.objects.filter(curveid=pump_trim_obj.marketing_data)
                .order_by("flow")
                .values_list("flow", flat=True)
            )
            heads = list(
                MarketingCurveData.objects.filter(curveid=pump_trim_obj.marketing_data)
                .order_by("flow")
                .values_list("head", flat=True)
            )
            powers = list(
                MarketingCurveData.objects.filter(curveid=pump_trim_obj.marketing_data)
                .order_by("flow")
                .values_list("power", flat=True)
            )
            bep_flow = getattr(pump_trim_obj.marketing_data, "bep_flow")
            flow_50 = 0.5 * bep_flow
            flow_75 = 0.75 * bep_flow
            flow_110 = 1.1 * bep_flow
            flow_120 = 1.2 * bep_flow

            headpoly = np.poly1d(np.polyfit(flows, heads, 6))
            powerpoly = np.poly1d(np.polyfit(flows, powers, 6))

            bep_head = headpoly(bep_flow)*3.28084
            head_50 = headpoly(flow_50)*3.28084
            head_75 = headpoly(flow_75)*3.28084
            head_110 = headpoly(flow_110)*3.28084

            bep_power = powerpoly(bep_flow)*1.34102
            power_50 = powerpoly(flow_50)*1.34102
            power_75 = powerpoly(flow_75)*1.34102
            power_110 = powerpoly(flow_110)*1.34102
            power_120 = powerpoly(flow_120)*1.34102

            flow_50 = flow_50*4.402862
            flow_75 = flow_75*4.402862
            flow_110 = flow_110*4.402862
            flow_120 =  flow_120*4.402862

            bep_eff = bep_flow*bep_head/(bep_power*3960)*100
            eff_50 = flow_50*head_50/(power_50*3960)*100
            eff_75 = flow_75*head_75/(power_75*3960)*100
            eff_110 = flow_110*head_110/(power_110*3960)*100

            if series == "FI":
                category = "ESCC"
            elif series == "CI":
                category = "ESFM"
            else:
                category = "IL"
            design_iteration = d.upper()
            if speed == 1760:
                nomspeed = 1800
                modelnumber = f"{series}{model}{design_iteration}-4P-PM"
                varspeedmodelnumber_1 = f"S{series}{model}{design_iteration}D-4P-PD"
                varspeedmodelnumber_2 = f"S{series}{model}{design_iteration}4-4P-PD"
            elif speed == 3500:
                nomspeed = 3600
                modelnumber = f"{series}{model}{design_iteration}-2P-PM"
                varspeedmodelnumber_1 = f"S{series}{model}{design_iteration}F-2P-PD"
                varspeedmodelnumber_2 = f"S{series}{model}{design_iteration}6-2P-PD"
            elif speed == 1160:
                nomspeed = 1200
                modelnumber = f"{series}{model}{design_iteration}-6P-PM"
                varspeedmodelnumber_1 = f"S{series}{model}{design_iteration}F-6P-PD"
                varspeedmodelnumber_2 = f"S{series}{model}{design_iteration}6-6P-PD"

            # pei = calculatePEI(
            #     bep_flow,
            #     bep_head,
            #     bep_power,
            #     flow_75,
            #     head_75,
            #     power_75,
            #     flow_110,
            #     head_110,
            #     power_110,
            #     power_120,
            #     speed,
            #     category,
            #     "BP"
            # )
            # pump_trim_obj.marketing_data.__dict__.update(peicl=pei['PEIcl'])
            # pump_trim_obj.marketing_data.__dict__.update(peivl=pei['PEIvl'])
            # pump_trim_obj.marketing_data.save()
            """
            return {
                "status": "success",
                "PEIcl": PEIcl,
                "PEIvl": PEIvl,
                "flow_bep": bep_flow_corr,
                "head_50": head_50_corr,
                "head_75": head_75_corr,
                "head_bep": bep_head_corr,
                "head_110": head_110_corr,
                "power_50": power_50_corr,
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

            # return_string += f"Taco, Taco, {series}{model}, {modelnumber}, {category}, Bare pump + motor, {trim}, 5, 1, {nomspeed}, , yes, {pei['motor_eff']}, {pei['motor_hp']}, yes, {pei['flow_bep']}, {pei['flow_bep']*0.75}, {pei['flow_bep']*1.1}, , , {pei['head_bep']}, , , , , {pei['power_bep']}, {pei['power_75']}, {pei['power_110']}, , , , , , , {pei['PEIcl']}, {pei['head_75']}, {pei['head_110']}, , , 109,\n"
            # return_string += f"Taco, Taco, S{series}{model}, {varspeedmodelnumber_1}, {category}, Bare pump + motor + continuous control, {trim}, 7, 1, {nomspeed}, , yes, {pei['motor_eff']}, {pei['motor_hp']}, yes, {pei['flow_bep']}, {pei['flow_bep']*0.75}, {pei['flow_bep']*1.1}, , , {pei['head_bep']}, , , , , , , , , , {pei['controller_power_25']}, {pei['controller_power_50']}, {pei['controller_power_75']}, {pei['controller_power_bep']}, {pei['PEIvl']}, {pei['head_75']}, {pei['head_110']}, , , 109,\n"
            # return_string += f"Taco, Taco, S{series}{model}, {varspeedmodelnumber_2}, {category}, Bare pump + motor + continuous control, {trim}, 7, 1, {nomspeed}, , yes, {pei['motor_eff']}, {pei['motor_hp']}, yes, {pei['flow_bep']}, {pei['flow_bep']*0.75}, {pei['flow_bep']*1.1}, , , {pei['head_bep']}, , , , , , , , , , {pei['controller_power_25']}, {pei['controller_power_50']}, {pei['controller_power_75']}, {pei['controller_power_bep']}, {pei['PEIvl']}, {pei['head_75']}, {pei['head_110']}, , , 109,\n"
            return_string += f"{series}{model}, {nomspeed}, {flow_50}, {head_50}, {eff_50}, {flow_75}, {head_75}, {eff_75}, {bep_flow}, {bep_head}, {bep_eff}, {flow_110}, {head_110}, {eff_110},\n"

    return HttpResponse(return_string, content_type="text/plain")


def populateCurveNos(request):
    pump_str = [
        ["CI", "1206", "D", 3500, 4179],
        ["CI", "1206", "D", 1760, 4180],
        ["CI", "1206", "D", 2900, 4181],
        ["CI", "1206", "D", 1450, 4182],
        ["CI", "1506", "D", 3500, 4188],
        ["CI", "1506", "D", 1760, 4189],
        ["CI", "1506", "D", 2900, 4190],
        ["CI", "1506", "D", 1450, 4191],
        ["CI", "1207", "D", 3500, 4183],
        ["CI", "1207", "D", 1760, 4184],
        ["CI", "1207", "D", 2900, 4185],
        ["CI", "1207", "D", 1450, 4186],
        ["CI", "1207", "D", 1160, 4187],
        ["CI", "1507", "D", 3500, 4192],
        ["CI", "1507", "D", 1760, 4193],
        ["CI", "1507", "D", 2900, 4194],
        ["CI", "1507", "D", 1450, 4195],
        ["CI", "1507", "D", 1160, 4196],
        ["CI", "1509", "D", 3500, 4197],
        ["CI", "1509", "D", 1760, 4198],
        ["CI", "1509", "D", 2900, 4199],
        ["CI", "1509", "D", 1450, 4200],
        ["CI", "1509", "D", 1160, 4201],
        ["CI", "2007", "D", 3500, 4202],
        ["CI", "2007", "D", 1760, 4203],
        ["CI", "2007", "D", 2900, 4204],
        ["CI", "2007", "D", 1450, 4205],
        ["CI", "2007", "D", 1160, 4206],
        ["CI", "2009", "D", 3500, 4207],
        ["CI", "2009", "D", 1760, 4208],
        ["CI", "2009", "D", 2900, 4209],
        ["CI", "2009", "D", 1450, 4210],
        ["CI", "2009", "D", 1160, 4211],
        ["CI", "2506", "D", 3500, 4212],
        ["CI", "2506", "D", 1760, 4214],
        ["CI", "2506", "D", 2900, 4213],
        ["CI", "2506", "D", 1450, 4215],
        ["CI", "2507", "D", 3500, 4216],
        ["CI", "2507", "D", 1760, 4218],
        ["CI", "2507", "D", 2900, 4217],
        ["CI", "2507", "D", 1450, 4219],
        ["CI", "2507", "D", 1160, 4220],
        ["CI", "2509", "D", 3500, 4221],
        ["CI", "2509", "D", 1760, 4223],
        ["CI", "2509", "D", 2900, 4222],
        ["CI", "2509", "D", 1450, 4224],
        ["CI", "2509", "D", 1160, 4225],
        ["CI", "2511", "D", 1760, 4226],
        ["CI", "2511", "D", 1450, 4227],
        ["CI", "2511", "D", 1160, 4228],
        ["CI", "2513", "D", 1760, 4229],
        ["CI", "2513", "D", 1450, 4230],
        ["CI", "2513", "D", 1160, 4231],
        ["CI", "3007", "D", 3500, 4232],
        ["CI", "3007", "D", 1760, 4234],
        ["CI", "3007", "D", 2900, 4233],
        ["CI", "3007", "D", 1450, 4235],
        ["CI", "3007", "D", 1160, 4236],
        ["CI", "3009", "D", 3500, 4237],
        ["CI", "3009", "D", 1760, 4239],
        ["CI", "3009", "D", 2900, 4238],
        ["CI", "3009", "D", 1450, 4240],
        ["CI", "3009", "D", 1160, 4241],
        ["CI", "3011", "D", 1760, 4242],
        ["CI", "3011", "D", 1450, 4243],
        ["CI", "3011", "D", 1160, 4244],
        ["CI", "3013", "D", 1760, 4245],
        ["CI", "3013", "D", 1450, 4246],
        ["CI", "3013", "D", 1160, 4247],
        ["CI", "4007", "D", 3500, 4248],
        ["CI", "4007", "D", 1760, 4250],
        ["CI", "4007", "D", 2900, 4249],
        ["CI", "4007", "D", 1450, 4251],
        ["CI", "4007", "D", 1160, 4252],
        ["CI", "4009", "D", 1760, 4253],
        ["CI", "4009", "D", 1450, 4254],
        ["CI", "4009", "D", 1160, 4255],
        ["CI", "4013", "D", 1760, 4256],
        ["CI", "4013", "D", 1450, 4257],
        ["CI", "4013", "D", 1160, 4258],
        ["CI", "5007", "D", 3500, 4259],
        ["CI", "5007", "D", 1760, 4261],
        ["CI", "5007", "D", 2900, 4260],
        ["CI", "5007", "D", 1450, 4262],
        ["CI", "5007", "D", 1160, 4263],
        ["CI", "5009", "D", 1760, 4264],
        ["CI", "5009", "D", 1450, 4265],
        ["CI", "5009", "D", 1160, 4266],
        ["CI", "5011", "D", 1760, 4267],
        ["CI", "5011", "D", 1450, 4268],
        ["CI", "5011", "D", 1160, 4269],
        ["CI", "6009", "D", 1760, 4270],
        ["CI", "6009", "D", 1450, 4271],
        ["CI", "6009", "D", 1160, 4272],
        ["CI", "6011", "D", 1760, 4273],
        ["CI", "6011", "D", 1450, 4274],
        ["CI", "6011", "D", 1160, 4275],
        ["CI", "1209", "D", 3500, 4276],
        ["CI", "1209", "D", 1760, 4278],
        ["CI", "1209", "D", 2900, 4277],
        ["CI", "1209", "D", 1450, 4279],
        ["CI", "1209", "D", 1160, 4280],
        ["CI", "1511", "D", 1760, 4281],
        ["CI", "1511", "D", 1450, 4282],
        ["CI", "1511", "D", 1160, 4283],
        ["CI", "4011", "D", 1760, 4284],
        ["CI", "4011", "D", 1450, 4285],
        ["CI", "4011", "D", 1160, 4286],
        ["CI", "2510", "D", 1760, 4287],
        ["CI", "2510", "D", 1450, 4288],
        ["CI", "2510", "D", 1160, 4289],
    ]
    for series, pumpmodel, design, speed, curve_number in pump_str:
        print(
            f"series:{series}; pumpmodel:{pumpmodel}; design:{design}; speed:{speed}; curvenumber:{curve_number}"
        )
        pumpObj = Pump.objects.filter(
            series=series,
            pump_model=pumpmodel,
            design_iteration=design,
            speed=speed,
        )
        print(pumpObj)
        pumpObj.update(
            curve_number=curve_number,
            curve_rev=f"PC-{curve_number} Rev -",
        )
    return HttpResponse(f"updated: \n{pump_str}", content_type="text/plain")
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


def populatePumps(request):
    pump_str = [
        ["CI", 2510, "C", 1160, [7.0, 10.0]],
        ["CI", 2510, "C", 1450, [7.0, 10.0]],
        ["CI", 2510, "C", 1760, [7.0, 10.0]],
        ["CI", 1209, "B", 1160, [6.7, 9.5]],
        ["CI", 1209, "B", 1450, [6.7, 9.5]],
        ["CI", 1209, "B", 1760, [6.7, 9.5]],
        ["CI", 1209, "B", 2900, [6.7, 9.5]],
        ["CI", 1209, "B", 3500, [6.7, 9.5]],
        ["CI", 1511, "B", 1160, [8.25, 11.25]],
        ["CI", 1511, "B", 1450, [8.25, 11.25]],
        ["CI", 1511, "B", 1760, [8.25, 11.25]],
        ["CI", 4011, "B", 1160, [8.0, 11.25]],
        ["CI", 4011, "B", 1450, [8.0, 11.25]],
        ["CI", 4011, "B", 1760, [8.0, 11.25]],
        ["KS", 1509, "C", 1160, [6.5, 9.5]],
        ["KS", 1509, "C", 1450, [6.5, 9.5]],
        ["KS", 1509, "C", 1760, [6.5]],
        ["KS", 1509, "C", 2900, [6.5, 9.5]],
        ["KS", 1509, "C", 3500, [6.5]],
        ["KS", 2011, "C", 1160, [8.25, 11.25]],
        ["KS", 2011, "C", 1450, [8.25, 11.25]],
        ["KS", 2011, "C", 1760, [8.25]]
    ]
    for series, pumpmodel, design, speed, trims in pump_str:
        print(
            f"series:{series}; pumpmodel:{pumpmodel}; design:{design}; speed:{speed}; trims:{trims}"
        )
        pumpObj = Pump.objects.create(
            series=series,
            pump_model=pumpmodel,
            design_iteration=design,
            speed=speed,
        )
        print(pumpObj)
        for trim in trims:
            pumpTrimObj = PumpTrim.objects.create(
                pump=pumpObj,
                trim=trim
            )

    return HttpResponse(f"updated: \n{pump_str}", content_type="text/plain")
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


def importOldDashboard(request):
    oldDataSources = list(OldTestDetails.objects.order_by().values_list('file_name', flat=True).distinct())
    # print(oldDataSources)
    for oldDataSource in oldDataSources:
        # if ".DBF" in oldDataSource:
        #     rawdata = RawTestsList.objects.filter(testname=oldDataSource[:-11])
        #     if rawdata.count():
        #         print(getattr(rawdata[0],'id'), getattr(rawdata[0], 'datareduced'))
        #         if not getattr(rawdata[0], 'datareduced'):
        #             pass
        if ".xlsx" in oldDataSource:
            excel_df = pd.read_excel(f'/home/atul_t/hydrodash/media/oldxlsx/{oldDataSource}')
            if 'Date' not in list(excel_df):
                print(f"No Date:{oldDataSource}")
            else:
                flow_title = ''
                head_title = ''
                temp_title = ''
                power_title = ''
                rpm_title = ''
                # Database to store values in SI Units with clear water at specific gravity 1.0
                # Flow - m3/hr
                # Head - m
                # Power - KW
                # Temperature - Kelvin

                flowunitconversionfactor = 0.227125
                headunitconversionfactor = 0.3048
                powerunitconversionfactor = 1

                if 'FM\\RPM' in list(excel_df) and 'FM\\POWER' in list(excel_df):
                    columns_to_save = ['Date', 'Time', 'FM\\FLOW', 'FM\\HEAD', 'FM\\SYST', 'FM\\POWER', 'FM\\RPM']
                    flow_title = 'FM\\FLOW'
                    head_title = 'FM\\HEAD'
                    temp_title = 'FM\\SYST'
                    power_title = 'FM\\POWER'
                    rpm_title = 'FM\\RPM'
                elif 'FM\\RPM' in list(excel_df) and 'FM\\HP' in list(excel_df):
                    columns_to_save = ['Date', 'Time', 'FM\\FLOW', 'FM\\HEAD', 'FM\\SYST', 'FM\\HP', 'FM\\RPM']
                    flow_title = 'FM\\FLOW'
                    head_title = 'FM\\HEAD'
                    temp_title = 'FM\\SYST'
                    power_title = 'FM\\HP'
                    rpm_title = 'FM\\RPM'
                    powerunitconversionfactor = .7457
                elif 'L4\\RPM' in list(excel_df) and 'FM\\HP' in list(excel_df):
                    columns_to_save = ['Date', 'Time', 'FM\\FLOW', 'FM\\HEAD', 'FM\\SYST', 'FM\\HP', 'L4\\RPM']
                    flow_title = 'FM\\FLOW'
                    head_title = 'FM\\HEAD'
                    temp_title = 'FM\\SYST'
                    power_title = 'FM\\HP'
                    rpm_title = 'L4\\RPM'
                    powerunitconversionfactor = .7457
                elif 'S2\\FLOW' in list(excel_df) and 'L4\\RPM' in list(excel_df):
                    columns_to_save = ['Date', 'Time', 'S2\\FLOW', 'S2\\HEAD', 'S2\\SYST', 'S2\\WATTS', 'L4\\RPM']
                    flow_title = 'S2\\FLOW'
                    head_title = 'S2\\HEAD'
                    temp_title = 'S2\\SYST'
                    power_title = 'S2\\WATTS'
                    rpm_title = 'L4\\RPM'
                    powerunitconversionfactor = 0.001
                elif 'S1\\FLOW' in list(excel_df):
                    columns_to_save = ['Date', 'Time', 'S1\\FLOW', 'S1\\HEAD', 'S1\\SYST', 'S1\\WATTS']
                    flow_title = 'S1\\FLOW'
                    head_title = 'S1\\HEAD'
                    temp_title = 'S1\\SYST'
                    power_title = 'S1\\WATTS'
                    powerunitconversionfactor = 0.001
                else:
                    print(f"No Match:{oldDataSource}")
                
                excel_df = excel_df[columns_to_save]

                oldDataObject = OldTestDetails.objects.filter(file_name=oldDataSource)[0]
                testname = getattr(oldDataObject, 'name')
                testeng = getattr(oldDataObject, 'testeng')
                teststnd = getattr(oldDataObject, 'teststnd')
                inpipedia_in = getattr(oldDataObject, 'inpipedia_in')
                outpipedia_in = getattr(oldDataObject, 'outpipedia_in')
                description = getattr(oldDataObject, 'description') + " __Auto_Imported"
                pump_type = getattr(oldDataObject, 'pump_type')
                testdate = str(excel_df['Date'].iloc[0])[:-9]+" "+excel_df['Time'].iloc[0]
                testdate = datetime.strptime(
                    testdate, "%Y-%m-%d %H:%M:%S.%f") + timedelta(hours=4)
                print(f'looking up: {testname}')
                if not ReducedPumpTestDetails.objects.filter(testname=testname).exists():
                    print(f'Inserting:\ntestname={testname},\ntesteng={testeng},\ntestloop={teststnd},\ndischarge_pipe_dia={outpipedia_in},\ninlet_pipe_dia={inpipedia_in},\ndescription={description},\ntestdate={testdate},\npumptype={pump_type},\nbearingframe=\'H\'')
                    testDetailsObj = ReducedPumpTestDetails.objects.create(
                        testname=testname,
                        testeng=testeng,
                        testloop=teststnd,
                        discharge_pipe_dia=outpipedia_in,
                        inlet_pipe_dia=inpipedia_in,
                        description=description,
                        testdate=testdate,
                        pumptype=pump_type,
                        bearingframe="H"
                    )
                    if rpm_title:
                        for index, row in excel_df.iterrows():
                            ReducedPumpTestData.objects.create(
                                testid = testDetailsObj,
                                flow = row[flow_title]*flowunitconversionfactor,
                                head = row[head_title]*headunitconversionfactor,
                                power = row[power_title]*powerunitconversionfactor,
                                temp = (row[temp_title]-32)*5/9,
                                rpm = row[rpm_title]
                            )
                    else:
                        for index, row in excel_df.iterrows():
                            ReducedPumpTestData.objects.create(
                                testid = testDetailsObj,
                                flow = row[flow_title]*flowunitconversionfactor,
                                head = row[head_title]*headunitconversionfactor,
                                power = row[power_title]*powerunitconversionfactor,
                                temp = (row[temp_title]-32)*5/9,
                                rpm = 0
                            )
                # print(oldDataSource)
                # break

    # if OldTestDetails.objects.filter(file_name=dbf_filename).count():
    #     oldtestdetailobj = OldTestDetails.objects.filter(file_name=dbf_filename).first()
    #     name = getattr(oldtestdetailobj, 'name')
    #     testeng = getattr(oldtestdetailobj, 'testeng')
    #     teststnd = getattr(oldtestdetailobj, 'teststnd')
    #     inpipedia_in = getattr(oldtestdetailobj, 'inpipedia_in')
    #     outpipedia_in = getattr(oldtestdetailobj, 'outpipedia_in')
    #     description = getattr(oldtestdetailobj, 'description')
    #     pump_type = getattr(oldtestdetailobj, 'pump_type')
    #     stand = "inside"
    return HttpResponse("DID IT")

