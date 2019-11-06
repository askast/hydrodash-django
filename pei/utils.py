import math


def yi(pow_i, motorHP):
    return (
        (-0.4508 * math.pow((pow_i / motorHP), 3))
        + (1.2399 * math.pow((pow_i / motorHP), 2))
        - (0.4301 * (pow_i / motorHP))
        + 0.6410
    )


def zi(power, motorHP):
    if motorHP <= 5:
        a = -0.4658
        b = 1.4965
        c = 0.5303
    elif 5 < motorHP <= 20:
        a = -1.3198
        b = 2.9551
        c = 0.1052
    elif 20 < motorHP <= 50:
        a = -1.5122
        b = 3.0777
        c = 0.1847
    else:
        a = -0.8914
        b = 2.8846
        c = 0.2625

    p_ratio = power / motorHP if power < motorHP else 1.0

    return a * math.pow(p_ratio, 2) + b * p_ratio + c


def calculatePEI(
    bep_flow,
    bep_head,
    bep_power,
    flow_75,
    head_75,
    power_75,
    flow_110,
    head_110,
    power_110,
    power_120,
    tempRPM,
    pump_type,
    test_type,
    motor_hp=0,
    motor_eff=0,
):
    bep_power = bep_power * 1.34102
    power_75 = power_75 * 1.34102
    power_110 = power_110 * 1.34102
    power_120 = power_120 * 1.34102

    bep_head = bep_head * 3.28084
    head_75 = head_75 * 3.28084
    head_110 = head_110 * 3.28084

    bep_flow = bep_flow * 4.402868
    flow_75 = flow_75 * 4.402868
    flow_110 = flow_110 * 4.402868

    if 1440 <= tempRPM <= 2160:
        nomspeed = 1800
    elif 2880 <= tempRPM <= 4320:
        nomspeed = 3600
    else:
        return {"status": "fail", "reason": "RPM not within range"}

    if nomspeed == 1800:
        if pump_type in ["ESCC", "CI"]:
            C_factor = 128.47
        elif pump_type in ["ESFM", "FI"]:
            C_factor = 128.85
        elif pump_type in ["IL", "KV", "KS", "TA"]:
            C_factor = 129.30
        elif pump_type in ["RSV"]:
            C_factor = 129.63
        elif pump_type in ["ST"]:
            C_factor = 138.78
        else:
            return {"status": "fail", "reason": "Pump type not recognized"}
    else:
        if pump_type in ["ESCC", "CI"]:
            C_factor = 130.42
        elif pump_type in ["ESFM", "FI"]:
            C_factor = 130.99
        elif pump_type in ["IL", "KV", "KS", "TA"]:
            C_factor = 133.84
        elif pump_type in ["RSV"]:
            C_factor = 133.20
        elif pump_type in ["ST"]:
            C_factor = 134.85
        else:
            return {"status": "fail", "reason": "Pump type not recognized"}

    bep_flow_corr = bep_flow * (nomspeed / tempRPM)
    bep_head_corr = bep_head * math.pow((nomspeed / tempRPM), 2)
    bep_power_corr = bep_power * math.pow((nomspeed / tempRPM), 3)
    flow_75_corr = flow_75 * (nomspeed / tempRPM)
    head_75_corr = head_75 * math.pow((nomspeed / tempRPM), 2)
    power_75_corr = power_75 * math.pow((nomspeed / tempRPM), 3)
    flow_110_corr = flow_110 * (nomspeed / tempRPM)
    head_110_corr = head_110 * math.pow((nomspeed / tempRPM), 2)
    power_110_corr = power_110 * math.pow((nomspeed / tempRPM), 3)
    power_120_corr = power_120 * math.pow((nomspeed / tempRPM), 3)

    specificSpeed = (
        nomspeed * math.pow(bep_flow_corr, 0.5) * math.pow(bep_head_corr, -0.75)
    )

    hydrobep_power = bep_flow_corr * bep_head_corr / 3956
    hydropower_75 = flow_75_corr * head_75_corr / 3956
    hydropower_110 = flow_110_corr * head_110_corr / 3956

    motorHPs = [
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
    ]
    motor_eff_1800 = [
        85.5,
        86.5,
        86.5,
        89.5,
        89.5,
        91.0,
        91.7,
        92.4,
        93.0,
        93.6,
        93.6,
        94.1,
        94.5,
        95.0,
        95.0,
        95.4,
        95.4,
        95.8,
        95.8,
        95.8,
    ]
    motor_eff_3600 = [
        77.0,
        84.0,
        85.5,
        85.5,
        86.5,
        88.5,
        89.5,
        90.2,
        91.0,
        91.7,
        91.7,
        92.4,
        93.0,
        93.6,
        93.6,
        93.6,
        94.1,
        94.1,
        95.0,
        95.0,
    ]

    if motor_hp == 0:
        for index, motorHP in enumerate(motorHPs):
            if motorHP > power_120_corr:
                break
    else:
        motorHP = motor_hp
        index = motorHPs.index(motor_hp)

    if motor_eff == 0:
        if nomspeed == 3600:
            motorEfficiency = motor_eff_3600[index]
        else:
            motorEfficiency = motor_eff_1800[index]
    else:
        motorEfficiency = motor_eff

    motorLossFull = (motorHP / (motorEfficiency / 100)) - motorHP

    STDEff = (
        -0.85 * math.pow(math.log(bep_flow_corr), 2)
        - 0.38 * math.log(specificSpeed) * math.log(bep_flow_corr)
        - 11.48 * math.pow(math.log(specificSpeed), 2)
        + 17.80 * math.log(bep_flow_corr)
        + 179.80 * math.log(specificSpeed)
        - (C_factor + 555.6)
    ) / 100

    partLoadLossBEP = motorLossFull * yi(bep_power_corr, motorHP)
    partLoadLoss75 = motorLossFull * yi(power_75_corr, motorHP)
    partLoadLoss110 = motorLossFull * yi(power_110_corr, motorHP)

    motorLossBEP = motorLossFull * yi(hydrobep_power / STDEff, motorHP)
    motorLoss75 = motorLossFull * yi(hydropower_75 / (STDEff * 0.95), motorHP)
    motorLoss110 = motorLossFull * yi(hydropower_110 / (STDEff * 0.985), motorHP)
    if test_type == "BP":
        drive_input_power_75 = power_75_corr + partLoadLoss75
        drive_input_power_bep = bep_power_corr + partLoadLossBEP
        drive_input_power_110 = power_110_corr + partLoadLoss110

    elif test_type == "PM":
        drive_input_power_75 = power_75_corr
        drive_input_power_bep = bep_power_corr
        drive_input_power_110 = power_110_corr
        bep_power_corr = drive_input_power_bep - partLoadLossBEP

    else:
        return {"status": "fail", "reason": "Test type unrecognized"}

    PERstd = (
        (hydropower_75 / (0.95 * STDEff) + motorLoss75) / 3
        + (hydrobep_power / STDEff + motorLossBEP) / 3
        + (hydropower_110 / (0.985 * STDEff) + motorLoss110) / 3
    )
    PERcl = (
        (drive_input_power_75) / 3
        + (drive_input_power_bep) / 3
        + (drive_input_power_110) / 3
    )
    PEIcl = PERcl / PERstd

    flow_25_corr = 0.25 * bep_flow_corr
    flow_50_corr = 0.5 * bep_flow_corr
    pump_input_power_25 = (
        0.80 * math.pow(flow_25_corr / bep_flow_corr, 3)
        + 0.20 * (flow_25_corr / bep_flow_corr)
    ) * bep_power_corr
    pump_input_power_50 = (
        0.80 * math.pow(flow_50_corr / bep_flow_corr, 3)
        + 0.20 * (flow_50_corr / bep_flow_corr)
    ) * bep_power_corr
    pump_input_power_75 = (
        0.80 * math.pow(flow_75_corr / bep_flow_corr, 3)
        + 0.20 * (flow_75_corr / bep_flow_corr)
    ) * bep_power_corr

    z_25 = zi(pump_input_power_25, motorHP)
    z_50 = zi(pump_input_power_50, motorHP)
    z_75 = zi(pump_input_power_75, motorHP)
    z_bep = zi(bep_power_corr, motorHP)

    motor_controller_loss_25 = motorLossFull * z_25
    motor_controller_loss_50 = motorLossFull * z_50
    motor_controller_loss_75 = motorLossFull * z_75
    motor_controller_loss_bep = motorLossFull * z_bep

    controller_input_power_25 = pump_input_power_25 + motor_controller_loss_25
    controller_input_power_50 = pump_input_power_50 + motor_controller_loss_50
    controller_input_power_75 = pump_input_power_75 + motor_controller_loss_75
    controller_input_power_bep = bep_power_corr + motor_controller_loss_bep

    PERvl = (
        0.25 * controller_input_power_25
        + 0.25 * controller_input_power_50
        + 0.25 * controller_input_power_75
        + 0.25 * controller_input_power_bep
    )
    PEIvl = PERvl / PERstd

    return {
        "status": "success",
        "PEIcl": PEIcl,
        "PEIvl": PEIvl,
        "flow_bep": bep_flow_corr,
        "head_75": head_75_corr,
        "head_bep": bep_head_corr,
        "head_110": head_110_corr,
        "power_75": drive_input_power_75,
        "power_bep": drive_input_power_bep,
        "power_110": drive_input_power_110,
        "controller_power_25": controller_input_power_25,
        "controller_power_50": controller_input_power_50,
        "controller_power_75": controller_input_power_75,
        "controller_power_bep": controller_input_power_bep,
        "motor_hp": motorHP,
        "motor_eff": motorEfficiency,
    }
