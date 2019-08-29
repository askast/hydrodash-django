import os
from collections import defaultdict as dd
from collections import OrderedDict
import collections
from datetime import datetime
from copy import deepcopy
from io import BytesIO
import base64
import math
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import lines
from matplotlib.cbook import get_sample_data
import matplotlib.tri as tri
from scipy.interpolate import InterpolatedUnivariateSpline
import csv

from django.http import JsonResponse
from django.views.generic.base import TemplateView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings
from django.core.files import File

from marketingdata.models import MarketingCurveDetail, MarketingCurveData
from .models import Pump, PumpTrim, NPSHData, SubmittalCurve, OldTestDetails

mpl.rcParams["font.size"] = 12


class PumpListView(TemplateView):
    template_name = "pump/pumplist.html"

    def get_context_data(self, **kwargs):

        trims_list = PumpTrim.objects.values(
            "pump__series",
            "pump__pump_model",
            "pump__design_iteration",
            "pump__speed",
            "trim",
            "marketing_data",
            "pump",
        )
        npsh_list = list(
            NPSHData.objects.all().values_list("pump", flat=True).distinct()
        )
        # load_old()

        nested_raw_trims = dd(lambda: dd(lambda: dd(lambda: dd(lambda: dd(list)))))
        for m in trims_list:
            if m["marketing_data"]:
                nested_raw_trims[m["pump__series"]][m["pump__pump_model"]][
                    m["pump__design_iteration"]
                ][m["pump__speed"]][m["trim"]] = [
                    getattr(
                        MarketingCurveDetail.objects.filter(
                            id=m["marketing_data"]
                        ).first(),
                        "peicl",
                    ),
                    getattr(
                        MarketingCurveDetail.objects.filter(
                            id=m["marketing_data"]
                        ).first(),
                        "peivl",
                    ),
                    m["pump"],
                ]
            else:
                nested_raw_trims[m["pump__series"]][m["pump__pump_model"]][
                    m["pump__design_iteration"]
                ][m["pump__speed"]][m["trim"]] = ["fail", "fail", m["pump"]]

        nested_trims = deepcopy(nested_raw_trims)

        for series, pumpmodels in nested_raw_trims.items():
            for pumpmodel, designs in pumpmodels.items():
                for design, speeds in designs.items():
                    nested_trims[series][pumpmodel][design]["hasalldata"] = True
                    for speed, trims in speeds.items():
                        nested_trims[series][pumpmodel][design][speed][
                            "hasalldata"
                        ] = True
                        nested_trims[series][pumpmodel][design][speed]["peicl"] = 0
                        nested_trims[series][pumpmodel][design][speed]["peivl"] = 0
                        if trims[list(trims.keys())[0]][2] in npsh_list:
                            nested_trims[series][pumpmodel][design][speed][
                                "NPSH"
                            ] = True
                        else:
                            nested_trims[series][pumpmodel][design][speed][
                                "NPSH"
                            ] = False
                            nested_trims[series][pumpmodel][design][speed][
                                "hasalldata"
                            ] = False
                            nested_trims[series][pumpmodel][design][
                                "hasalldata"
                            ] = False

                        for trim, peis in trims.items():
                            if peis[0] is "fail":
                                nested_trims[series][pumpmodel][design][
                                    "hasalldata"
                                ] = False
                                nested_trims[series][pumpmodel][design][speed][
                                    "hasalldata"
                                ] = False
                                nested_trims[series][pumpmodel][design][speed][
                                    trim
                                ] = False
                            else:
                                nested_trims[series][pumpmodel][design][speed][
                                    trim
                                ] = True
                                if peis[0]:
                                    nested_trims[series][pumpmodel][design][speed][
                                        "peicl"
                                    ] = peis[0]
                                    nested_trims[series][pumpmodel][design][speed][
                                        "peivl"
                                    ] = peis[1]
                                else:
                                    if (
                                        "peicl"
                                        not in nested_trims[series][pumpmodel][design][
                                            speed
                                        ].keys()
                                    ):
                                        nested_trims[series][pumpmodel][design][speed][
                                            "peicl"
                                        ] = 0
                                        nested_trims[series][pumpmodel][design][speed][
                                            "peivl"
                                        ] = 0

        nested_trims = sortOD(convert(default_to_regular(nested_trims)))

        # print(nested_trims)
        context = {
            "name": self.request.user.get_full_name(),
            "title1": "Hydro Dash",
            "activedropdown": "",
            "activename": "Pumps Listing",
            "pumpmodels": nested_trims,
        }
        return context


def default_to_regular(d):
    if isinstance(d, dd):
        d = {k: default_to_regular(v) for k, v in d.items()}
    return d


def convert(data):
    if isinstance(data, str):
        return data
    elif isinstance(data, int) or isinstance(data, float):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.items()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data


def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res


def createSubmittalCurves(request):
    def convert_ax_ft_to_m(ax_ft):
        """
        Update second axis according with first axis.
        """
        y1, y2 = ax_ft.get_ylim()
        ax_m.set_ylim(ft2m(y1), ft2m(y2))
        ax_kpa.set_ylim(ft2kpa(y1), ft2kpa(y2))
        x1, x2 = ax_ft.get_xlim()
        ax_l.set_xlim(gpm2lps(x1), gpm2lps(x2))
        # print("y1:"+str(y1)+" y2:"+str(y2)+" kpay1:"+str(ft2kpa(y1))+" kpay2:"+str(ft2kpa(y2)))

        ax_m.figure.canvas.draw()

    def convert_ax_npsh_to_kpa(ax_npsh):
        """
        Update second axis according with first axis.
        """
        y1, y2 = ax_npsh.get_ylim()
        ax_npsh_kpa.set_ylim(ft2kpa(y1), ft2kpa(y2))

        ax_npsh_kpa.figure.canvas.draw()

    def convert_ax_npsh_to_m(ax_npsh):
        """
        Update second axis according with first axis.
        """
        y1, y2 = ax_npsh.get_ylim()
        ax_npsh_m.set_ylim(ft2m(y1), ft2m(y2))
        ax_npsh_m.figure.canvas.draw()

    series = request.POST.get("series", None)
    pumpmodel = request.POST.get("model", None)
    design = request.POST.get("design", None)
    rpm = request.POST.get("rpm", None)

    max_motor_hp_string = request.POST.get("maxhp", None)
    min_motor_hp_string = request.POST.get("minhp", None)
    eff_levels_string = request.POST.get("efflevels", None)
    power_manual_locations_string = request.POST.get("powerlocs", None)
    x_axis_limit_string = request.POST.get("xlim", None)
    y_axis_limit_string = request.POST.get("ylim", None)

    pumpobj = Pump.objects.get(
        series=series, pump_model=pumpmodel, design_iteration=design, speed=rpm
    )
    # if not check if any config is empty but pumpobj exists in database, send the most recent to screen. along with ids of other configs.
    # if it doesnt exist in database, make best guesses for config. and generate the curve.

    curveObjs = (
        PumpTrim.objects.filter(pump=pumpobj)
        .order_by("marketing_data__imp_dia")
        .values("trim", "marketing_data")
    )

    npsh_data = NPSHData.objects.filter(pump=pumpobj).values("flow", "npsh")
    npsh_data = np.array(
        [[point["flow"] * 4.402862, point["npsh"] * 3.28084] for point in npsh_data]
    )
    npsh_data = npsh_data[np.argsort(npsh_data[:, 0])]

    # check if this exact config exists. if it does send the curve as response. along with ids of other configs with same pump.
    submittal_curves_list = []
    if SubmittalCurve.objects.filter(pump=pumpobj).count():
        submittal_curves_list = list(
            SubmittalCurve.objects.filter(pump=pumpobj)
            .order_by("-id")
            .values_list("id", flat=True)
        )
        submittal_curve_obj = (
            SubmittalCurve.objects.filter(pump=pumpobj).order_by("-id").first()
        )
        if not max_motor_hp_string:
            max_motor_hp_string = str(getattr(submittal_curve_obj, "max_motor_hp"))
        if not min_motor_hp_string:
            min_motor_hp_string = str(getattr(submittal_curve_obj, "min_motor_hp"))
        if not eff_levels_string:
            eff_levels_string = ", ".join(
                map(str, getattr(submittal_curve_obj, "eff_levels"))
            )
        if not power_manual_locations_string:
            power_manual_locations_string = ""
            for flow, head in zip(
                getattr(submittal_curve_obj, "power_manual_location_flows"),
                getattr(submittal_curve_obj, "power_manual_location_heads"),
            ):
                power_manual_locations_string += f"({flow},{head}),"
            power_manual_locations_string = power_manual_locations_string[:-1]
        if not x_axis_limit_string:
            x_axis_limit_string = str(getattr(submittal_curve_obj, "x_axis_limit"))
        if not y_axis_limit_string:
            y_axis_limit_string = str(getattr(submittal_curve_obj, "y_axis_limit"))

    diameters = []
    curveids = []
    for curveObj in curveObjs:
        trim = curveObj["trim"]
        curve = curveObj["marketing_data"]
        diameters.append(trim)
        curveids.append(curve)

    bep_flow = []
    bep_head = []
    bep_eff = []
    head_polys = []
    eff_polys = []
    eff_coeffs = []
    power_polys = []
    peicl = 0
    peivl = 0
    for curve in curveids:
        # print(f'curve:{curve}')
        curve = MarketingCurveDetail.objects.filter(id=curve).first()
        bep_flow.append(getattr(curve, "bep_flow") * 4.402862)
        bep_head.append(getattr(curve, "bep_head") * 3.28084)
        bep_eff.append(getattr(curve, "bep_efficiency") * 100)
        head_polys.append(np.poly1d(getattr(curve, "headcoeffs")))
        eff_polys.append(np.poly1d(getattr(curve, "effcoeffs")))
        eff_coeffs.append(getattr(curve, "effcoeffs"))
        power_polys.append(np.poly1d(getattr(curve, "powercoeffs")))
        temp_peicl = getattr(curve, "peicl")
        temp_peivl = getattr(curve, "peivl")
        if temp_peicl != 0 and temp_peivl != 0:
            peicl = temp_peicl
            peivl = temp_peivl

    bep_flow = bep_flow[-1]
    bep_head = bep_head[-1]
    bep_eff = bep_eff[-1]

    std_motor_hps = [
        0.5,
        0.75,
        1,
        1.5,
        2,
        3,
        5,
        7.5,
        10,
        15,
        20,
        25,
        30,
        40,
        50,
        60,
        75,
        100,
        125,
        150,
        200,
        250,
        300,
        350,
        400,
        450,
        500,
        600,
        700,
        800,
        900,
        1000,
        1250,
        1500,
        1750,
        2000,
        2250,
        2500,
        3000,
    ]
    print(f'maxhp:{max_motor_hp_string}')
    if not max_motor_hp_string:
        max_trim_max_hp = (
            MarketingCurveData.objects.filter(
                curveid=MarketingCurveDetail.objects.get(id=curveids[-1])
            )
            .order_by("-power")
            .values_list("power", flat=True)[0]
            * 1.34102
        )
        max_motor_hp = min(hp for hp in std_motor_hps if hp > max_trim_max_hp)
        max_motor_hp_string = str(max_motor_hp)
    else:
        max_motor_hp = float(max_motor_hp_string)

    if not min_motor_hp_string:
        min_trim_max_hp = (
            MarketingCurveData.objects.filter(
                curveid=MarketingCurveDetail.objects.get(id=curveids[0])
            )
            .order_by("-power")
            .values_list("power", flat=True)[0]
            * 1.34102
        )
        min_motor_hp = min(hp for hp in std_motor_hps if hp > min_trim_max_hp)
        min_motor_hp_string = str(min_motor_hp)
    else:
        min_motor_hp = float(min_motor_hp_string)

    power_levels = np.array(
        [hp for hp in std_motor_hps if min_motor_hp <= hp <= max_motor_hp],
        dtype=np.float64,
    )

    if not eff_levels_string:
        eff_levels = np.array(
            [
                int(round(0.78 * bep_eff, 0)),
                int(round(0.85 * bep_eff, 0)),
                int(round(0.91 * bep_eff, 0)),
                int(round(0.945 * bep_eff, 0)),
                int(round(0.975 * bep_eff, 0)),
                int(round(bep_eff - 1, 0)),
            ],
            dtype=np.float64,
        )
        eff_levels_string = ", ".join(
                map(str, eff_levels)
            )
    else:
        eff_levels = np.array(
            [float(x) for x in eff_levels_string.split(",")], dtype=np.float64
        )

    full_trim_flow_min = 0
    full_trim_flow_max = (
        MarketingCurveData.objects.filter(
            curveid=MarketingCurveDetail.objects.get(id=curveids[-1])
        )
        .order_by("-flow")
        .values_list("flow", flat=True)[0]
        * 4.402862
    )

    if not power_manual_locations_string:
        power_loc_flows = np.linspace(0, full_trim_flow_max, len(power_levels))
        power_loc_flows = np.around(power_loc_flows, 0)
        power_loc_heads = np.linspace(0, bep_head, len(power_levels))
        power_loc_heads = np.around(power_loc_heads, 0)
        power_manual_locations = []
        power_manual_location_flows = []
        power_manual_location_heads = []
        for flow, head in zip(power_loc_flows, power_loc_heads):
            power_manual_locations.append((flow, head))
            power_manual_location_flows.append(flow)
            power_manual_location_heads.append(head)
        power_manual_locations_string = ""
        for flow, head in zip(power_manual_location_flows, power_manual_location_heads):
            power_manual_locations_string += f"({flow},{head}),"
        power_manual_locations_string = power_manual_locations_string[:-1]
    else:
        power_manual_locations_strings = power_manual_locations_string.replace(
            " ", ""
        ).split("),(")
        power_manual_locations = []
        power_manual_location_flows = []
        power_manual_location_heads = []
        for string in power_manual_locations_strings:
            string = string.replace("(", "").replace(")", "")
            power_loc_flow, power_loc_head = string.split(",")
            power_manual_locations.append(
                (float(power_loc_flow), float(power_loc_head))
            )
            power_manual_location_flows.append(float(power_loc_flow))
            power_manual_location_heads.append(float(power_loc_head))

    if not x_axis_limit_string:
        x_axis_limits = [0, full_trim_flow_max * 1.1]
        x_axis_limits = np.around(x_axis_limits, 0)
        x_axis_limit_string = str(x_axis_limits[1])
    else:
        x_axis_limits = [0, float(x_axis_limit_string)]

    if not y_axis_limit_string:
        y_axis_limits = [0, bep_head * 1.3]
        y_axis_limits = np.around(y_axis_limits, 0)
        y_axis_limit_string = str(y_axis_limits[1])
    else:
        y_axis_limits = [0, float(y_axis_limit_string)]

    if SubmittalCurve.objects.filter(
            pump=pumpobj,
            max_motor_hp=max_motor_hp,
            min_motor_hp=min_motor_hp,
            eff_levels=list(eff_levels),
            power_manual_location_flows=power_manual_location_flows,
            power_manual_location_heads=power_manual_location_heads,
            x_axis_limit=x_axis_limits[1],
            y_axis_limit=y_axis_limits[1],
            curve_ids=curveids,
            npsh_flows=list(npsh_data.T[0] / 4.402862),
            npsh_npshs=list(npsh_data.T[1] / 3.28084),
        ).count():
        submittal_curve_obj = SubmittalCurve.objects.get(
            pump=pumpobj,
            max_motor_hp=max_motor_hp,
            min_motor_hp=min_motor_hp,
            eff_levels=list(eff_levels),
            power_manual_location_flows=power_manual_location_flows,
            power_manual_location_heads=power_manual_location_heads,
            x_axis_limit=x_axis_limits[1],
            y_axis_limit=y_axis_limits[1],
            curve_ids=curveids,
            npsh_flows=list(npsh_data.T[0] / 4.402862),
            npsh_npshs=list(npsh_data.T[1] / 3.28084),
        )
        graphic = base64.b64encode(submittal_curve_obj.curve_svg.read())
        graphic = graphic.decode("utf-8")

        context = {
            "status": "success",
            "plot": graphic,
            "maxhp": max_motor_hp_string,
            "minhp": min_motor_hp_string,
            "efflevels": eff_levels_string,
            "powerlocs": power_manual_locations_string,
            "xlim": x_axis_limit_string,
            "ylim": y_axis_limit_string,
            "pdflink": submittal_curve_obj.curve_pdf.url
        }

        return JsonResponse(context)

    newcurve = SubmittalCurve(
        pump=pumpobj,
        max_motor_hp=max_motor_hp,
        min_motor_hp=min_motor_hp,
        eff_levels=list(eff_levels),
        power_manual_location_flows=power_manual_location_flows,
        power_manual_location_heads=power_manual_location_heads,
        x_axis_limit=x_axis_limits[1],
        y_axis_limit=y_axis_limits[1],
        created_on=datetime.now(),
        curve_ids=curveids,
        npsh_flows=list(npsh_data.T[0] / 4.402862),
        npsh_npshs=list(npsh_data.T[1] / 3.28084),
    )
    newcurve.save()
    curveid = getattr(newcurve, "id")
    submittal_curves_list.append(curveid)
    isopower_cutoff_percent = 15
    curve_rec = Pump.objects.filter(
        series=series, pump_model=pumpmodel, design_iteration=design, speed=rpm
    ).first()
    curveno = getattr(curve_rec, "curve_number")
    curverev = getattr(curve_rec, "curve_rev")
    curvedate = datetime.now().strftime(r"%B %d, %Y")
    inletdia, dischargedia = PumpTrim.objects.filter(
        pump__series=series,
        pump__pump_model=pumpmodel,
        pump__design_iteration=design,
        pump__speed=rpm,
    ).values_list(
        "marketing_data__data_source__inlet_pipe_dia",
        "marketing_data__data_source__discharge_pipe_dia",
    )[
        0
    ]

    inletdia = ("%f" % round_pipe_dia(inletdia)).rstrip("0").rstrip(".")
    dischargedia = ("%f" % round_pipe_dia(dischargedia)).rstrip("0").rstrip(".")

    # Lower it to move left. Use .1 if it doesnt interfere with other axis tags
    l_per_sec_offset = 0.04

    diameter_label_flow_offset = 0.01 * bep_flow
    diameter_label_head_offset = 0.02 * bep_head

    sp_gr_position = [bep_flow * 0.04, bep_head * 0.05]
    req_npsh_position = [bep_flow * 0.5, np.amax(npsh_data.T[1]) / 2]

    a_max = head_polys[-1](full_trim_flow_max).item() / pow(full_trim_flow_max, 2)
    temp_flows = np.linspace(0, (full_trim_flow_max + 5), 100)
    temp_poly_heads_max = np.power(temp_flows, 2) * a_max
    # print(f'polyheads: {poly_heads}')
    curve_heads = [head_polys[i](temp_flows) for i in range(len(head_polys))]
    # curve_powers = [fpowers[i](temp_flows) for i in range(len(fheads))]
    # curve_effs = [feffs[i](temp_flows) for i in range(len(fheads))]
    intercept_flowheads_max = [
        interpolated_intercept(temp_flows, temp_poly_heads_max, curve_heads[i])
        for i in range(len(head_polys))
    ]

    if full_trim_flow_min > 0:
        a_min = head_polys[-1](full_trim_flow_min).item() / pow(full_trim_flow_min, 2)
        temp_flows = np.linspace(0, (full_trim_flow_min + 5), 100)
        temp_poly_heads_min = np.power(temp_flows, 2) * a_min
        # print(f'polyheads: {poly_heads}')
        curve_heads = [head_polys[i](temp_flows) for i in range(len(head_polys))]
        # curve_powers = [fpowers[i](temp_flows) for i in range(len(fheads))]
        # curve_effs = [feffs[i](temp_flows) for i in range(len(fheads))]
        intercept_flowheads_min = [
            interpolated_intercept(temp_flows, temp_poly_heads_min, curve_heads[i])
            for i in range(len(head_polys))
        ]
    else:
        intercept_flowheads_min = [(0, 0) for i in range(len(head_polys))]

    flow_min_cutoffs = []
    flow_max_cutoffs = []
    for ((min_flow, min_head), (max_flow, max_head)) in zip(
        intercept_flowheads_min, intercept_flowheads_max
    ):
        flow_min_cutoffs.append(min_flow)
        flow_max_cutoffs.append(max_flow)

    plot_flows = [
        np.linspace(flow_min, flow_max, 200)
        for flow_min, flow_max in zip(flow_min_cutoffs, flow_max_cutoffs)
    ]
    plot_heads = [
        head_poly(plot_flow) for plot_flow, head_poly in zip(plot_flows, head_polys)
    ]
    # plot_effs = [eff_poly(plot_flow) for plot_flow, eff_poly in zip(plot_flows, eff_polys)]

    logo = plt.imread(
        get_sample_data(
            settings.BASE_DIR + staticfiles_storage.url("profiles/img/logo.png")
        )
    )

    plt.rc("font", family="Assistant")
    fig, (ax_npsh, ax_ft) = plt.subplots(
        2, sharex=True, gridspec_kw={"height_ratios": [1, 4], "hspace": 0.115}
    )

    ax_m = ax_ft.twinx()
    ax_l = ax_m.twiny()
    ax_kpa = ax_l.twinx()
    fig.subplots_adjust(right=0.87, top=0.875, bottom=0.175)
    ax_kpa.spines["right"].set_position(("axes", 1.08))
    fig.set_size_inches(11, 8.5)

    ax_kpa.set_frame_on(True)
    ax_kpa.patch.set_visible(False)

    ax_npsh_m = ax_npsh.twinx()
    ax_npsh_kpa = ax_npsh.twinx()
    ax_npsh_kpa.spines["right"].set_position(("axes", 1.075))
    ax_npsh.grid(b=True, which="major", color="k", linestyle="-", linewidth=0.75)
    ax_npsh.grid(b=True, which="minor", color="#C0C0C0", linestyle="-", linewidth=0.75)
    ax_npsh.minorticks_on()

    # automatically update ylim of ax2 when ylim of ax1 changes.
    ax_ft.callbacks.connect("ylim_changed", convert_ax_ft_to_m)
    ax_ft.callbacks.connect("xlim_changed", convert_ax_ft_to_m)
    ax_npsh.callbacks.connect("ylim_changed", convert_ax_npsh_to_kpa)
    ax_npsh.callbacks.connect("ylim_changed", convert_ax_npsh_to_m)
    x_npsh = np.linspace(np.amin(npsh_data.T[0]), np.amax(npsh_data.T[0]), 300)
    npsh_spline = InterpolatedUnivariateSpline(npsh_data.T[0], npsh_data.T[1])
    smooth_npsh = npsh_spline(x_npsh)
    ax_npsh.plot(x_npsh, smooth_npsh, color="k", linewidth=0.75)

    for i in range(len(diameters)):
        ax_ft.plot(
            plot_flows[i],
            plot_heads[i],
            color="k",
            label="{:1.3f}".format(diameters[i]).rstrip("0").rstrip(".")
            + '"({:1.0f}mm)'.format(diameters[i] * 25.4),
            linewidth=1.0,
        )

    ax_ft.set_xlim(x_axis_limits)
    ax_ft.set_ylim(y_axis_limits)
    ax_ft.set_xlabel("FLOW IN GALLONS PER MINUTE", fontsize=15)
    ax_ft.set_ylabel("HEAD IN FEET", fontsize=15)
    ax_l.set_xlabel("L/SEC", fontsize=12)
    ax_l.xaxis.set_label_coords(l_per_sec_offset, 1.0175)
    ax_l.tick_params(direction="out", pad=0)
    ax_m.set_ylabel("HEAD IN METERS", fontsize=12)
    ax_kpa.set_ylabel("HEAD IN KILOPASCALS", fontsize=12)
    ax_ft.grid(b=True, which="major", color="k", linestyle="-", linewidth=0.75)
    ax_ft.grid(b=True, which="minor", color="#C0C0C0", linestyle="-", linewidth=0.75)
    ax_ft.minorticks_on()
    my_legend(
        ax_ft,
        diameter_label_flow_offset=diameter_label_flow_offset,
        plot_heads=plot_heads,
        diameter_label_head_offset=diameter_label_head_offset,
    )
    ax_ft.text(
        sp_gr_position[0],
        sp_gr_position[1],
        "CURVES BASED ON CLEAR WATER\nWITH SPECIFIC GRAVITY OF 1.0",
        fontsize=14,
        bbox=dict(facecolor="white", edgecolor="none", pad=0.0),
        ha="left",
        va="bottom",
    )

    ax_npsh.set_ylabel("FEET", fontsize=12)
    ax_npsh_m.set_ylabel("METERS", fontsize=12)
    ax_npsh_kpa.set_ylabel("KPA", fontsize=12)
    y1, y2 = ax_npsh.get_ylim()
    ax_npsh.set_ylim(0, y2)
    ax_npsh.text(
        req_npsh_position[0],
        req_npsh_position[1],
        "REQUIRED NPSH",
        fontsize=14,
        bbox=dict(facecolor="white", edgecolor="none", pad=0.0),
        ha="left",
        va="bottom",
    )

    for label in ax_ft.xaxis.get_majorticklabels():
        label.set_fontsize(14)
    for label in ax_ft.yaxis.get_majorticklabels():
        label.set_fontsize(14)
    for label in ax_npsh.yaxis.get_majorticklabels():
        label.set_fontsize(14)
    for label in ax_l.xaxis.get_majorticklabels():
        label.set_fontsize(14)
    for label in ax_m.yaxis.get_majorticklabels():
        label.set_fontsize(14)
    for label in ax_kpa.yaxis.get_majorticklabels():
        label.set_fontsize(14)
    for label in ax_npsh_m.yaxis.get_majorticklabels():
        label.set_fontsize(14)
    for label in ax_npsh_kpa.yaxis.get_majorticklabels():
        label.set_fontsize(14)

    x1, x2 = ax_ft.get_xlim()
    ax_ft.set_xlim(0, x2)
    y1, y2 = ax_ft.get_ylim()
    ax_ft.set_ylim(0, y2 + 2)

    eff_lab_x, eff_lab_y = efficiency_label_points(
        pch0=head_polys[-1],
        poly_eff_coeffs_0=eff_coeffs[-1],
        eff_levels=eff_levels,
        flow_min_cutoffs=flow_min_cutoffs,
        flow_max_cutoffs=flow_max_cutoffs,
    )
    # print(f'eff_labx:{eff_lab_x}\neff_lab_y:{eff_lab_y}')
    flowpoints_for_eff_contour, headpoints_for_eff_contour, effpoints_for_eff_contour, flowpoints_for_pow_contour, headpoints_for_pow_contour, powpoints_for_pow_contour, = get_points_mesh(
        flow_max_cutoffs=flow_max_cutoffs,
        fheads=head_polys,
        feffs=eff_polys,
        fpowers=power_polys,
    )

    triang_eff = tri.Triangulation(
        flowpoints_for_eff_contour, headpoints_for_eff_contour
    )

    fheadsmall = InterpolatedUnivariateSpline(plot_flows[0], plot_heads[0])
    # Mask off unwanted triangles.
    xmid = np.array(flowpoints_for_eff_contour)[triang_eff.triangles].mean(axis=1)
    ymid = np.array(headpoints_for_eff_contour)[triang_eff.triangles].mean(axis=1)
    mask = np.where(ymid < fheadsmall(xmid), 1, 0)
    triang_eff.set_mask(mask)

    ax_ft.tricontour(
        triang_eff,
        effpoints_for_eff_contour,
        levels=eff_levels,
        colors="k",
        linewidths=0.5,
    )

    for flow, head, eff in zip(
        eff_lab_x, eff_lab_y, np.concatenate([eff_levels, eff_levels[::-1]])
    ):
        if eff.is_integer():
            eff_str = str(int(eff))
        else:
            eff_str = str(eff)
        ax_ft.text(
            flow + 1,
            head + 0.25,
            eff_str + "%",
            rotation=45,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.0),
            ha="left",
            va="bottom",
        )

    triang_pow = tri.Triangulation(
        flowpoints_for_pow_contour, headpoints_for_pow_contour
    )

    # Mask off unwanted triangles.
    xmid_pow = np.array(flowpoints_for_pow_contour)[triang_pow.triangles].mean(axis=1)
    mask_pow = np.where(xmid_pow < bep_flow * isopower_cutoff_percent / 100, 1, 0)
    triang_pow.set_mask(mask_pow)

    CS_power = ax_ft.tricontour(
        triang_pow,
        powpoints_for_pow_contour,
        levels=power_levels,
        colors="k",
        linewidths=0.5,
    )

    fmt = {}
    for l in power_levels:
        fmt[l] = (
            "{:1.2f}".format(l).rstrip("0").rstrip(".")
            + "HP({:1.2f}".format(l * 0.7457).rstrip("0").rstrip(".")
            + "KW)"
        )

    power_labels = ax_ft.clabel(
        CS_power, inline=False, fontsize=10, manual=power_manual_locations, fmt=fmt
    )

    for txt in power_labels:
        txt.set_bbox(dict(facecolor="white", edgecolor="none", pad=0))

    for c in CS_power.collections:
        c.set_dashes([(0, (6.0, 6.0))])

    newax = fig.add_axes([0.13, 0.885, 0.175, 0.175], anchor="SE", zorder=-1)
    newax.imshow(logo)
    newax.axis("off")

    newax2 = fig.add_axes([0.31, 0.85, 0.875, 0.2], anchor="SE", zorder=-1)
    newax2.axis("off")

    x, y = np.array([[0.0, 0.635], [0.45, 0.45]])
    line = lines.Line2D(x, y, lw=1, color="k")
    newax2.add_line(line)

    plt.gcf().text(
        0.31,
        0.98,
        f"{series} Series | Model: {pumpmodel}{design} | {rpm} RPM",
        fontsize=24,
        weight="bold",
    )
    plt.gcf().text(
        0.31,
        0.95,
        f'Curve No. {curveno} | Min. Imp. Dia. {min(diameters)}" | Size {inletdia}x{dischargedia}x{max(diameters)} | {curvedate}',
        fontsize=14,
        weight="normal",
    )
    plt.gcf().text(
        0.31,
        0.915,
        f"Energy Efficiency Rating:",
        fontsize=14,
        weight="bold",
        color="green",
    )
    if peicl != 0:
        plt.gcf().text(
            0.515,
            0.915,
            r"Pump & Motor: $\mathregular{PEI_{CL}}$: "
            + str(round(peicl, 2))
            + r" | $\mathregular{ER_{CL}}$: "
            + str(int(round((1 - peicl) * 100, 0))),
            fontsize=14,
            weight="normal",
            color="green",
        )
        plt.gcf().text(
            0.515,
            0.89,
            r"Pump, Motor & Drive: $\mathregular{PEI_{VL}}$: "
            + str(round(peivl, 2))
            + r" | $\mathregular{ER_{VL}}$: "
            + str(int(round((1 - peivl) * 100, 0))),
            fontsize=14,
            weight="normal",
            color="green",
        )
    else:
        plt.gcf().text(
            0.515,
            0.915,
            r"Pump & Motor: $\mathregular{PEI_{CL}}$: N/A @1160RPM",
            fontsize=14,
            weight="normal",
            color="green",
        )
        plt.gcf().text(
            0.515,
            0.89,
            r"Pump, Motor & Drive: $\mathregular{PEI_{VL}}$: N/A @1160RPM",
            fontsize=14,
            weight="normal",
            color="green",
        )

    plt.gcf().text(
        0.7825, 0.125, f"{curverev}        {curveid}", fontsize=7, weight="normal", color="k"
    )

    fine_max_eff = bep_eff
    fine_max_eff_flow = bep_flow
    fine_max_eff_head = bep_head
    ax_ft.plot(fine_max_eff_flow, fine_max_eff_head, marker="|", color="k")
    ax_ft.text(
        fine_max_eff_flow + 1,
        fine_max_eff_head + 0.25,
        "{:1.1f}".format(round_of_eff(fine_max_eff)).rstrip("0").rstrip(".") + "%",
        rotation=45,
        bbox=dict(facecolor="white", edgecolor="none", pad=0.0),
        ha="left",
        va="bottom",
    )

    for plot_flow, plot_head in zip(plot_flows, plot_heads):
        ax_ft.plot(plot_flow, plot_head, "--", color="k", linewidth=0.5)

    fig.patch.set_facecolor("xkcd:mint green")

    name = f"{series}{pumpmodel}{design}_{rpm}RPM"
    plt.savefig(
        settings.BASE_DIR + f"/media/Outputs/{name}.jpg", format="jpg", dpi=1000
    )
    # print("Outputs\\" + name + ".jpg file created")

    pdf_buffer = BytesIO()
    plt.savefig(pdf_buffer, format="pdf", dpi=1000, bbox_inches="tight")
    pdf_buffer.seek(0)
    newcurve.curve_pdf.save(f"{curveid}-{name}.pdf", File(pdf_buffer))
    pdf_buffer.close()
    svg_buffer = BytesIO()
    plt.savefig(svg_buffer, format="svg", dpi=1000, bbox_inches="tight")
    svg_buffer.seek(0)
    newcurve.curve_svg.save(f"{curveid}-{name}.svg", File(svg_buffer))
    image_svg = svg_buffer.getvalue()
    svg_buffer.close()

    graphic = base64.b64encode(image_svg)
    graphic = graphic.decode("utf-8")

    context = {
        "status": "success",
        "plot": graphic,
        "maxhp": max_motor_hp_string,
        "minhp": min_motor_hp_string,
        "efflevels": eff_levels_string,
        "powerlocs": power_manual_locations_string,
        "xlim": x_axis_limit_string,
        "ylim": y_axis_limit_string,
        "pdflink": newcurve.curve_pdf.url
    }

    return JsonResponse(context)


def efficiency_label_points(
        pch0, poly_eff_coeffs_0, eff_levels, flow_min_cutoffs, flow_max_cutoffs
    ):
    flow = []
    head = []
    for eff in eff_levels:
        # print(f'polyeffcoeffs:{poly_eff_coeffs_0}')
        # print(f'eff:{eff}')
        adjusted_poly_eff_coeffs_0 = deepcopy(poly_eff_coeffs_0)
        adjusted_poly_eff_coeffs_0[-1] -= eff / 100
        root = np.poly1d(adjusted_poly_eff_coeffs_0).roots
        root = root[np.isreal(root)]
        # print("Roots: ", end="")
        # print(root)
        for item in root:
            # print(f'roots:{item}')
            # print(f'min:{flow_min_cutoffs[-1]}')
            # print(f'max:{flow_max_cutoffs[-1]}')
            if flow_min_cutoffs[-1] < item < flow_max_cutoffs[-1]:
                flow.append(np.real(item))
                head.append(np.real(np.poly1d(pch0)(item)))
    flow = np.array(flow)
    head = np.array(head)
    p = flow.argsort()
    return flow[p], head[p]


def my_legend(axis, diameter_label_flow_offset, plot_heads, diameter_label_head_offset):
    for index, line in enumerate(axis.lines):
        axis.text(
            diameter_label_flow_offset,
            np.amax(plot_heads[index]) + diameter_label_head_offset,
            line.get_label(),
            bbox=dict(facecolor="white", edgecolor="none", pad=0.0),
        )


def ft2m(head):
    return head * 0.3048


def ft2kpa(head):
    return head * 2.98898


def gpm2lps(flow):
    return flow * 0.06309


def round_of_eff(number):
    return round(number * 2) / 2


def round_pipe_dia(x):
    return 0.5 * round(x / 0.5)


# def intercept(x, y1, y2):
#     idx = np.argwhere(np.diff(np.sign(y1 - y2))).flatten()
#     return (x[idx], y1[idx])


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


def get_points_mesh(flow_max_cutoffs, fheads, feffs, fpowers):

    top_flows = list(np.linspace(0, flow_max_cutoffs[-1], 81))[1:]
    bottom_flows = list(np.linspace(0, flow_max_cutoffs[0], 81))[1:]
    # print(f'top flows:{top_flows}\nbottom flows:{bottom_flows}')

    polys = [
        fheads[-1](top_flow1).item() / math.pow(top_flow1, 2) for top_flow1 in top_flows
    ]

    top_heads = [fheads[-1](top_flow1).item() for top_flow1 in top_flows]
    bottom_heads = [fheads[0](bottom_flow1).item() for bottom_flow1 in bottom_flows]
    # print(f'top heads:{top_heads}\nbottom heads:{bottom_heads}')

    flowmesh_for_eff_contour = []
    headmesh_for_eff_contour = []
    effmesh_for_eff_contour = []

    flowmesh_for_power_contour = []
    headmesh_for_power_contour = []
    powermesh_for_power_contour = []

    for a, top_flow in zip(polys, top_flows):
        # print(f'polys: {polys}\ntop_flows: {top_flows}')
        temp_flows = np.linspace(0, (top_flow * 1.05), 100)
        poly_heads = np.power(temp_flows, 2) * a
        # print(f'polyheads: {poly_heads}')
        curve_heads = [fheads[i](temp_flows) for i in range(len(fheads))]
        # curve_powers = [fpowers[i](temp_flows) for i in range(len(fheads))]
        # curve_effs = [feffs[i](temp_flows) for i in range(len(fheads))]
        intercept_flowheads = [
            interpolated_intercept(temp_flows, poly_heads, curve_heads[i])
            for i in range(len(fheads))
        ]
        # print(f"intercepts_flowheads: {intercept_flowheads}")

        temp_poly_flows = np.linspace(intercept_flowheads[0][0], top_flow, 20)
        temp_poly_heads = np.power(temp_poly_flows, 2) * a

        temp_intercept_flows = [
            np.take(intercept_flowheads[i][0], 0) for i in range(len(fheads))
        ]
        temp_intercept_powers = [
            fpowers[i](temp_intercept_flows[i]) for i in range(len(fheads))
        ]
        temp_intercept_effs = [
            feffs[i](temp_intercept_flows[i]) for i in range(len(fheads))
        ]
        # print(f"temp_intercepts_flows: {temp_intercept_flows}")
        power_poly = np.poly1d(
            np.polyfit(temp_intercept_flows, temp_intercept_powers, 2)
        )
        eff_poly = np.poly1d(np.polyfit(temp_intercept_flows, temp_intercept_effs, 2))
        temp_poly_powers = power_poly(temp_poly_flows)
        temp_poly_effs = eff_poly(temp_poly_flows)
        for flowpoint, headpoint, powerpoint, effpoint in zip(
            temp_poly_flows, temp_poly_heads, temp_poly_powers, temp_poly_effs
        ):
            flowmesh_for_eff_contour.append(flowpoint.item())
            headmesh_for_eff_contour.append(headpoint.item())
            effmesh_for_eff_contour.append(effpoint.item() * 100)
    # print(f'eff_mesh:{effmesh_for_eff_contour}')
    top_flows = list(np.linspace(0, flow_max_cutoffs[-1], 81))[1:]

    polys = [
        fheads[-1](top_flow1).item() / math.pow(top_flow1, 2) for top_flow1 in top_flows
    ]
    # [
    #     print(f'topflow:{top_flow1}; tophead:{fheads[-1](top_flow1).item()}') for top_flow1 in top_flows
    # ]
    max_head = max(top_heads)
    min_head = min(bottom_heads)

    for a, top_flow in zip(polys, top_flows):
        # print(
        #     f'polys: {polys}\ntop_flows: {top_flows}\ntop_heads: {top_heads}')
        # print(f'max_head:{max_head}; a:{a}')
        poly_max_flow = math.sqrt(max_head / a)
        poly_min_flow = math.sqrt(min_head / a)
        temp_flows = np.linspace(0, (poly_max_flow * 1.05), 100)
        poly_heads = np.power(temp_flows, 2) * a
        curve_heads = [fheads[i](temp_flows) for i in range(len(fheads))]
        # curve_powers = [fpowers[i](temp_flows) for i in range(len(fheads))]
        # curve_effs = [feffs[i](temp_flows) for i in range(len(fheads))]
        flowheads = [
            interpolated_intercept(temp_flows, poly_heads, curve_heads[i])
            for i in range(len(fheads))
        ]
        # print(f"intercepts_flowheads: {intercept_flowheads}")

        temp_poly_flows = np.linspace(poly_min_flow, poly_max_flow, 20)
        temp_poly_heads = np.power(temp_poly_flows, 2) * a

        temp_intercept_flows = [np.take(flowheads[i][0], 0) for i in range(len(fheads))]
        temp_intercept_powers = [
            fpowers[i](temp_intercept_flows[i]) for i in range(len(fheads))
        ]
        temp_intercept_effs = [
            feffs[i](temp_intercept_flows[i]) for i in range(len(fheads))
        ]
        # print(f"temp_intercepts_flows: {temp_intercept_flows}")
        power_poly = np.poly1d(
            np.polyfit(temp_intercept_flows, temp_intercept_powers, 2)
        )
        eff_poly = np.poly1d(np.polyfit(temp_intercept_flows, temp_intercept_effs, 2))
        temp_poly_powers = power_poly(temp_poly_flows)
        temp_poly_effs = eff_poly(temp_poly_flows)
        for flowpoint, headpoint, powerpoint, effpoint in zip(
            temp_poly_flows, temp_poly_heads, temp_poly_powers, temp_poly_effs
        ):
            flowmesh_for_power_contour.append(flowpoint.item())
            headmesh_for_power_contour.append(headpoint.item())
            powermesh_for_power_contour.append(powerpoint.item())

    return (
        flowmesh_for_eff_contour,
        headmesh_for_eff_contour,
        effmesh_for_eff_contour,
        flowmesh_for_power_contour,
        headmesh_for_power_contour,
        powermesh_for_power_contour,
    )


def load_old():
    path = settings.BASE_DIR + staticfiles_storage.url(
        "profiles/img/testdetailsexport.csv"
    )
    with open(path) as f:
        reader = csv.reader(f)
        for row in reader:
            print(
                f"name={row[1]}\ntesteng={row[2]}\nteststnd={row[3]}\ninpipedia_in={row[4]}\noutpipedia_in={row[5]}\ndescription={row[6]}\ntestconfigs_id={row[7]}\npump_type={row[8]}\ncreated_at={row[9]}\nupdated_at={row[10]}\nfile_name={row[11]}\naveraged={row[12]}"
            )
            print("#####################################################")
            _, created = OldTestDetails.objects.get_or_create(
                name=row[1],
                testeng=row[2],
                teststnd=row[3],
                inpipedia_in=row[4],
                outpipedia_in=row[5],
                description=row[6],
                testconfigs_id=row[7],
                pump_type=row[8],
                created_at=row[9],
                updated_at=row[10],
                file_name=row[11],
                averaged=row[12],
            )
            # creates a tuple of the new object or
            # current object and a boolean of if it was created
