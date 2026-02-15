# src/engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .models import (
    adjust_c_for_continuity_at_knee,
    calendar_dqdt,
    cycling_dqdt_post_knee,
    cycling_dqdt_pre_knee,
    resistance_drdt,
)


@dataclass
class Params:
    # simulation
    threshold: float
    time_step: float

    # environment/load
    T_kelvin: float
    I: float

    # capacity nominal
    b: float

    # phase schedule
    calendar_duration: float
    cycling_duration: float

    # constants/model params
    R_gas: float

    z_calendar: float
    b_calendar: float
    E_calendar: float

    z_resistance: float
    b_resistance: float
    E_resistance: float

    a_cycling: float
    z_cycling: float
    z_cycling_knee: float
    E_cycling: float

    Q_critical: float

    # knee / continuity
    c_init: float

    # resistance scaling
    resistance_scale_cycling: float = 1.0


def run_simulation(p: Params) -> pd.DataFrame:

    # initial state
    capacity = p.b
    current_time = 0.0
    total_throughput = 0.0

    Q_percentage = 0.0
    R_percentage = 0.01

    Q_loss_calendar = 0.0
    Q_loss_cycling = 0.05

    FCE_knee = 0.1
    c = p.c_init
    knee_adjusted = False  # replaces your "a == 2" switch

    # histories
    rows: List[Dict[str, Any]] = []

    # main loop
    while Q_percentage < p.threshold:
        # FCE definition (your script uses total_throughput/b)
        FCE = total_throughput / p.b

        # Determine phase (calendar vs cycling)
        phase_t = current_time % (p.calendar_duration + p.cycling_duration)
        in_calendar = phase_t < p.calendar_duration

        if in_calendar:
            dQdt = calendar_dqdt(
                Q_percentage,
                z_calendar=p.z_calendar,
                b_calendar=p.b_calendar,
                E_calendar=p.E_calendar,
                R_gas=p.R_gas,
                T_kelvin=p.T_kelvin,
            )
            Q_loss_calendar += dQdt * p.time_step * p.b

            dRdt_cal = resistance_drdt(
                R_percentage,
                z_resistance=p.z_resistance,
                b_resistance=p.b_resistance,
                E_resistance=p.E_resistance,
                R_gas=p.R_gas,
                T_kelvin=p.T_kelvin,
            )
            dRdt_cyc = 0.0

        else:
            # cycling phase
            if Q_percentage < p.Q_critical:
                # your script computes a t_from_Q for a special pre-critical expression;
                # BUT then uses an expression that is effectively the pre-knee form.
                # To keep the refactor safe, we’ll use the same pre-knee dqdt in terms of FCE
                # unless you explicitly want the t_from_Q pathway preserved.
                dQdt = cycling_dqdt_pre_knee(
                    FCE,
                    I=p.I,
                    b=p.b,
                    a_cycling=p.a_cycling,
                    z_cycling=p.z_cycling,
                    E_cycling=p.E_cycling,
                    R_gas=p.R_gas,
                    T_kelvin=p.T_kelvin,
                )
                throughput_at_knee = total_throughput
                FCE_knee = throughput_at_knee / p.b
            else:
                # knee handling (your old: if a == 2)
                if not knee_adjusted:
                    FCE_knee = total_throughput / p.b
                    c = adjust_c_for_continuity_at_knee(
                        FCE_knee,
                        I=p.I,
                        b=p.b,
                        a_cycling=p.a_cycling,
                        z_cycling=p.z_cycling,
                        z_cycling_knee=p.z_cycling_knee,
                        c=c,
                        E_cycling=p.E_cycling,
                        R_gas=p.R_gas,
                        T_kelvin=p.T_kelvin,
                    )
                    knee_adjusted = True

                dQdt = cycling_dqdt_post_knee(
                    FCE,
                    FCE_knee,
                    I=p.I,
                    b=p.b,
                    c=c,
                    z_cycling_knee=p.z_cycling_knee,
                    E_cycling=p.E_cycling,
                    R_gas=p.R_gas,
                    T_kelvin=p.T_kelvin,
                )

            Q_loss_cycling += abs(dQdt) * p.time_step * p.b

            dRdt_cyc = resistance_drdt(
                R_percentage,
                z_resistance=p.z_resistance,
                b_resistance=p.b_resistance,
                E_resistance=p.E_resistance,
                R_gas=p.R_gas,
                T_kelvin=p.T_kelvin,
            )
            dRdt_cal = 0.0

            # throughput accumulation during cycling (factor of 2 in your script because of charge/discharge)
            total_throughput += p.I * p.time_step / 3600.0 * 0.5

        # update state (same as your script)
        capacity = capacity - abs(dQdt) * p.b * p.time_step

        R_percentage += (
            dRdt_cal * p.time_step * 100.0
            + dRdt_cyc * p.time_step * 100.0 * p.resistance_scale_cycling
        )

        if current_time > 0:
            Q_percentage = (p.b - capacity) / p.b * 100.0

        current_time += p.time_step

        rows.append(
            {
                "t_s": current_time,
                "t_week": current_time / (3600.0 * 24.0 * 7.0),
                "phase": "calendar" if in_calendar else "cycling",
                "FCE": FCE,
                "FCE_knee": FCE_knee,
                "capacity_Ah": capacity,
                "Q_loss_pct": Q_percentage,
                "dQdt": abs(dQdt),
                "R_pct": R_percentage,
                "dRdt_cal": dRdt_cal,
                "dRdt_cyc": dRdt_cyc,
                "throughput_Ah": total_throughput,
                "knee_adjusted": knee_adjusted,
                "c": c,
                "Q_loss_calendar_Ah": Q_loss_calendar,
                "Q_loss_cycling_Ah": Q_loss_cycling,
            }
        )

    return pd.DataFrame(rows)
