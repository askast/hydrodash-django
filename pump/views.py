from collections import defaultdict as dd
from collections import OrderedDict
import collections
from copy import deepcopy
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cbook import get_sample_data
import matplotlib.tri as tri
from scipy.interpolate import InterpolatedUnivariateSpline

from django.views.generic.base import TemplateView

from .models import Pump, PumpTrim, NPSHData
from marketingdata.models import MarketingCurveDetail


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
        )
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
                ]
            else:
                nested_raw_trims[m["pump__series"]][m["pump__pump_model"]][
                    m["pump__design_iteration"]
                ][m["pump__speed"]][m["trim"]] = ["fail", "fail"]

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

        print(nested_trims)
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
    curveObjs = PumpTrim.objects.filter(
        pump__series=series,
        pump__pump_model=pumpmodel,
        pump__design_iteration=design,
        pump__speed=rpm,
    ).values(
        "trim",
        "marketing_data"
    )
    npsh_data = NPSHData.objects.filter(
        pump__series=series,
        pump__pump_model=pumpmodel,
        pump__design_iteration=design,
        pump__speed=rpm,
    ).values(
        "flow",
        "npsh"
    )
    diameters = []
    curveids = []
    for trim, curve in curveObjs:
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
        bep_flow.append(getattr(curve, "bep_flow"))
        bep_head.append(getattr(curve, "bep_head"))
        bep_eff.append(getattr(curve, "bep_efficiency"))
        head_polys.append(np.poly1d(getattr(curve, "headcoeffs")))
        eff_polys.append(np.poly1d(getattr(curve, "effcoeffs")))
        eff_coeffs.append(getattr(curve, "effcoeffs"))
        power_polys.append(np.poly1d(getattr(curve, "powercoeffs")))
        temp_peicl = getattr(curve, "peicl")
        temp_peivl = getattr(curve, "peivl")
        if temp_peicl != 0 and temp_peivl != 0:
            peicl = temp_peicl
            peivl = temp_peivl

    flow_min_cutoffs = [0, 0, 0, 0, 0]
    flow_max_cutoffs = [210, 190, 175, 150, 125]

    sp_gr_position = [5, 5]
    req_npsh_position = [500, 5]
    eff_levels = np.array([55, 60, 64, 66, 68, 69], dtype=np.float64)
    power_levels = np.array([3, 5, 7.5, 10], dtype=np.float64)
    power_manual_locations = [(125, 30), (165, 60), (190, 65), (175, 160)]
    x_axis_limits = [0, 225]
    y_axis_limits = [0, 200]
    efficiency_plot_scale = 0.35
    # Lower it to move left. Use .1 if it doesnt interfere with other axis tags
    l_per_sec_offset = 0.08
    diameter_label_flow_offset = 2
    diameter_label_head_offset = 4
    max_eff_insert = True  # Set this to True or False

    plot_flows = [np.linspace(flow_min, flow_max, 200) for flow_min, flow_max in zip(flow_min_cutoffs, flow_max_cutoffs)]
    plot_heads = [head_poly(plot_flow) for plot_flow, head_poly in zip(plot_flow, head_polys)]
    plot_effs = [eff_poly(plot_flow) for plot_flow, eff_poly in zip(plot_flow, eff_polys)]
    plot_powers = [power_poly(plot_flow) for plot_flow, power_poly in zip(plot_flow, power_polys)]
    # plot_effs = []
    # plot_pows = []
    # beps = []

    logo = plt.imread(get_sample_data("../profiles/statuc/profiles/img/logo.png"))

    npsh_data = np.array([[point["flow"], point["npsh"]] for point in npsh_data])
    plt.rc("font", family="Assistant")
    fig, (ax_npsh, ax_ft) = plt.subplots(
        2, sharex=True, gridspec_kw={"height_ratios": [1, 4], "hspace": 0.1}
    )

    ax_m = ax_ft.twinx()
    ax_l = ax_m.twiny()
    ax_kpa = ax_l.twinx()
    fig.subplots_adjust(right=0.83, top=0.8, bottom=0.175)
    ax_kpa.spines["right"].set_position(("axes", 1.075))
    fig.set_size_inches(11, 8.5)

    ax_kpa.set_frame_on(True)
    ax_kpa.patch.set_visible(False)

    ax_npsh_m = ax_npsh.twinx()
    ax_npsh_kpa = ax_npsh.twinx()
    ax_npsh_kpa.spines["right"].set_position(("axes", 1.075))
    ax_npsh.grid(b=True, which="major", color="k", linestyle="-", linewidth=0.75)
    ax_npsh.grid(b=True, which="minor", color="k", linestyle="-", linewidth=0.1)
    ax_npsh.minorticks_on()

    # automatically update ylim of ax2 when ylim of ax1 changes.
    ax_ft.callbacks.connect("ylim_changed", convert_ax_ft_to_m)
    ax_ft.callbacks.connect("xlim_changed", convert_ax_ft_to_m)
    ax_npsh.callbacks.connect("ylim_changed", convert_ax_npsh_to_kpa)
    ax_npsh.callbacks.connect("ylim_changed", convert_ax_npsh_to_m)
    x_npsh = np.linspace(np.amin(npsh_data[0]), np.amax(npsh_data[0]), 300)
    npsh_spline = InterpolatedUnivariateSpline(npsh_data[0], npsh_data[1])
    smooth_npsh = npsh_spline(x_npsh)
    ax_npsh.plot(x_npsh, smooth_npsh, color="k", linewidth=0.75)

    [
        ax_ft.plot(
            plot_flows[i],
            plot_heads[i],
            color="k",
            label="{:1.3f}".format(diameters[i]).rstrip("0").rstrip(".")
            + '"({:1.0f}mm)'.format(diameters[i] * 25.4),
            linewidth=1.0,
        )
        for i in range(len(diameters))
    ]
    ax_ft.set_xlim(x_axis_limits)
    ax_ft.set_ylim(y_axis_limits)
    ax_ft.set_xlabel("FLOW IN GALLONS PER MINUTE", fontsize=15)
    ax_ft.set_ylabel("HEAD IN FEET", fontsize=15)
    ax_l.set_xlabel("L/SEC", fontsize=12)
    ax_l.xaxis.set_label_coords(l_per_sec_offset, 1.015)
    ax_l.tick_params(direction="out", pad=0)
    ax_m.set_ylabel("HEAD IN METERS", fontsize=12)
    ax_kpa.set_ylabel("HEAD IN KILOPASCALS", fontsize=12)
    ax_ft.grid(b=True, which="major", color="k", linestyle="-", linewidth=0.75)
    ax_ft.grid(b=True, which="minor", color="k", linestyle="-", linewidth=0.1)
    ax_ft.minorticks_on()
    my_legend(ax_ft, diameter_label_flow_offset=diameter_label_flow_offset, plot_heads=plot_heads, diameter_label_head_offset=diameter_label_head_offset)
    ax_ft.text(
        sp_gr_position[0],
        sp_gr_position[1],
        "CURVES BASED ON CLEAR WATER\nWITH SPECIFIC GRAVITY OF 1.0",
        fontsize=12,
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
        fontsize=12,
        bbox=dict(facecolor="white", edgecolor="none", pad=0.0),
        ha="left",
        va="bottom",
    )

    [tick.label.set_fontsize(14) for tick in ax_ft.xaxis.get_major_ticks()]
    [tick.label.set_fontsize(14) for tick in ax_ft.yaxis.get_major_ticks()]

    x1, x2 = ax_ft.get_xlim()
    ax_ft.set_xlim(0, x2)
    y1, y2 = ax_ft.get_ylim()
    ax_ft.set_ylim(0, y2 + 2)

    eff_lab_x, eff_lab_y = efficiency_label_points(pch0=head_polys[0], poly_eff_coeffs_0=eff_coeffs[0], eff_levels=eff_levels, flow_min_cutoffs=flow_max_cutoffs, flow_max_cutoffs=flow_max_cutoffs)

    flowpoints_for_eff_contour, headpoints_for_eff_contour, effpoints_for_eff_contour, flowpoints_for_pow_contour, headpoints_for_pow_contour, powpoints_for_pow_contour, = (
        get_points_mesh(flow_max_cutoffs=flow_max_cutoffs, fheads=head_polys, feffs=eff_polys, fpowers=power_polys)
    )

    triang_eff = tri.Triangulation(
        flowpoints_for_eff_contour, headpoints_for_eff_contour
    )

    fheadsmall = InterpolatedUnivariateSpline(plot_flows[-1], plot_heads[-1])
    # Mask off unwanted triangles.
    xmid = np.array(flowpoints_for_eff_contour)[triang_eff.triangles].mean(axis=1)
    ymid = np.array(headpoints_for_eff_contour)[triang_eff.triangles].mean(axis=1)
    mask = np.where(ymid < fheadsmall(xmid), 1, 0)
    triang_eff.set_mask(mask)

    CS_eff = ax_ft.tricontour(
        triang_eff,
        effpoints_for_eff_contour,
        levels=eff_levels,
        colors="k",
        linewidths=0.5,
    )
    # eff_labels = ax_ft.clabel(CS_eff, inline=False, fontsize=6)

    for flow, head, eff in zip(eff_lab_x, eff_lab_y, np.concatenate([eff_levels, eff_levels[::-1]])):
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
    mask_pow = np.where(xmid_pow < 25, 1, 0)
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
        CS_power, inline=False, fontsize=8, manual=power_manual_locations, fmt=fmt
    )
    [
        txt.set_bbox(dict(facecolor="white", edgecolor="none", pad=0))
        for txt in power_labels
    ]

    for c in CS_power.collections:
        c.set_dashes([(0, (6.0, 6.0))])

    # newax = fig.add_axes([0.13, 0.79, 0.16, 0.16], anchor='SE', zorder=-1)
    # newax.imshow(logo)
    # newax.axis('off')
    series = request.POST.get("series", None)
    pumpmodel = request.POST.get("model", None)
    design = request.POST.get("design", None)
    rpm = request.POST.get("rpm", None)

    name = f"{series}{pumpmodel}{design}_{rpm}RPM"
    plt.gcf().text(0.3, 0.88, f"MODEL: {series}{pumpmodel}{design} {rpm}RPM", fontsize=20)

    if max_eff_insert:
        fine_max_eff = bep_eff[0]
        fine_max_eff_flow = bep_flow[0]
        fine_max_eff_head = bep_head[0]
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

    for plot_flow, plot_head, plot_eff in zip(plot_flows, plot_heads, plot_effs):
        ax_ft.plot(plot_flow, plot_head, "--", color="k", linewidth=0.5)
        # pce = poly1d(efficiency_coefficients)
        # ax_ft.plot(Flow, pce(Flow)*efficiency_plot_scale,
        #             '--', color='g', linewidth=0.5)

    plt.savefig(f"media/Outputs/{name}.eps", format="eps", dpi=1000)
    print("Outputs\\" + name + ".eps file created")
    plt.savefig(f"media/Outputs/{name}.jpg", format="jpg", dpi=1000)
    print("Outputs\\" + name + ".jpg file created")
    # with open('Outputs\\'+base_name+'.json', "w") as outfile:
    #     json.dump({'head_coeff':ph, 'eff_coeff':pe.tolist()}, outfile, indent=4)


def efficiency_label_points(pch0, poly_eff_coeffs_0, eff_levels, flow_min_cutoffs, flow_max_cutoffs):
    flow = []
    head = []
    for eff in eff_levels:
        poly_eff_coeffs_0[-1] -= eff
        root = np.poly1d(poly_eff_coeffs_0).roots
        root = root[np.isreal(root)]
        # print("Roots: ", end="")
        # print(root)
        for item in root:
            if (
                item > flow_min_cutoffs[0]
                and item < flow_max_cutoffs[0]
            ):
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
    return xc, yc


def get_points_mesh(flow_max_cutoffs, fheads, feffs, fpowers):

    top_flows = list(np.linspace(0, flow_max_cutoffs[0], 81))[1:]
    bottom_flows = list(np.linspace(0, flow_max_cutoffs[-1], 81))[1:]

    polys = [
        fheads[0](top_flow1).item() / math.pow(top_flow1, 2) for top_flow1 in top_flows
    ]

    top_heads = [fheads[0](top_flow1).item() for top_flow1 in top_flows]
    bottom_heads = [fheads[-1](bottom_flow1).item() for bottom_flow1 in bottom_flows]

    flowmesh_for_eff_contour = []
    headmesh_for_eff_contour = []
    effmesh_for_eff_contour = []

    flowmesh_for_power_contour = []
    headmesh_for_power_contour = []
    powermesh_for_power_contour = []

    for a, top_flow in zip(polys, top_flows):
        # print(
        #     f'polys: {polys}\ntop_flows: {top_flows}\ntop_heads: {top_heads}')
        temp_flows = np.linspace(0, top_flow + 5, 100)
        poly_heads = np.power(temp_flows, 2) * a
        curve_heads = [fheads[i](temp_flows) for i in range(len(fheads))]
        curve_powers = [fpowers[i](temp_flows) for i in range(len(fheads))]
        curve_effs = [feffs[i](temp_flows) for i in range(len(fheads))]
        intercept_flowheads = [
            interpolated_intercept(temp_flows, poly_heads, curve_heads[i])
            for i in range(len(fheads))
        ]
        # print(f"intercepts_flowheads: {intercept_flowheads}")

        temp_poly_flows = np.linspace(intercept_flowheads[-1][0], top_flow, 20)
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
            effmesh_for_eff_contour.append(effpoint.item())

    top_flows = list(np.linspace(0, flow_max_cutoffs[0], 81))[1:]

    polys = [
        fheads[0](top_flow1).item() / math.pow(top_flow1, 2) for top_flow1 in top_flows
    ]

    max_head = max(top_heads)
    min_head = min(bottom_heads)

    for a, top_flow in zip(polys, top_flows):
        # print(
        #     f'polys: {polys}\ntop_flows: {top_flows}\ntop_heads: {top_heads}')
        poly_max_flow = math.sqrt(max_head / a)
        poly_min_flow = math.sqrt(min_head / a)
        temp_flows = np.linspace(0, poly_max_flow, 100)
        poly_heads = np.power(temp_flows, 2) * a
        curve_heads = [fheads[i](temp_flows) for i in range(len(fheads))]
        curve_powers = [fpowers[i](temp_flows) for i in range(len(fheads))]
        curve_effs = [feffs[i](temp_flows) for i in range(len(fheads))]
        intercept_flowheads = [
            interpolated_intercept(temp_flows, poly_heads, curve_heads[i])
            for i in range(len(fheads))
        ]
        # print(f"intercepts_flowheads: {intercept_flowheads}")

        temp_poly_flows = np.linspace(poly_min_flow, poly_max_flow, 20)
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

