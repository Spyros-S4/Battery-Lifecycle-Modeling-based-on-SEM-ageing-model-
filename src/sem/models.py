# src/models.py
import numpy as np

SECONDS_PER_WEEK = 604800.0

def calendar_dqdt(
    Q_percentage: float, *, z_calendar, b_calendar, E_calendar, R_gas, T_kelvin
) -> float:

    # Returns dQ/dt (fraction of capacity per second, in your current formulation),
    # including the /100 and /week conversion exactly as in the original script.

    return (
        z_calendar
        * b_calendar
        * np.exp(-E_calendar / (R_gas * T_kelvin))
        * (Q_percentage / (b_calendar * np.exp(-E_calendar / (R_gas * T_kelvin))))
        ** (1 - 1 / z_calendar)
        / 100.0
        / SECONDS_PER_WEEK
    )

def resistance_drdt(
    R_percentage: float, *, z_resistance, b_resistance, E_resistance, R_gas, T_kelvin
) -> float:

    # Returns dR/dt (percentage per second in your formulation), including /100 and /week conversion.

    return (
        z_resistance
        * b_resistance
        * np.exp(-E_resistance / (R_gas * T_kelvin))
        * (R_percentage / (b_resistance * np.exp(-E_resistance / (R_gas * T_kelvin))))
        ** (1 - 1 / z_resistance)
        / 100.0
        / SECONDS_PER_WEEK
    )

def cycling_dqdt_pre_knee(
    FCE: float, *, I, b, a_cycling, z_cycling, E_cycling, R_gas, T_kelvin
) -> float:

    # Pre-knee cycling dQ/dt expression you use (the one based on FCE^(z-1)).

    return (
        (I / (3600.0 * 2.0 * b))
        * a_cycling
        * z_cycling
        * np.exp(-E_cycling / (R_gas * T_kelvin))
        * (FCE ** (z_cycling - 1.0))
        / b
    )

def cycling_dqdt_post_knee(
    FCE: float, FCE_knee: float, *, I, b, c, z_cycling_knee, E_cycling, R_gas, T_kelvin
) -> float:

    # Post-knee exponential form.

    return (
        (I / (3600.0 * 2.0 * b))
        * z_cycling_knee
        * c
        * np.exp(-E_cycling / (R_gas * T_kelvin))
        * np.exp(z_cycling_knee * (FCE - FCE_knee))
        / b
    )

def adjust_c_for_continuity_at_knee(
    FCE_knee: float,
    *,
    I,
    b,
    a_cycling,
    z_cycling,
    z_cycling_knee,
    c,
    E_cycling,
    R_gas,
    T_kelvin
) -> float:

    # Your original “adjust c so dQdt_before == dQdt_after at knee”.

    d_before = cycling_dqdt_pre_knee(
        FCE_knee,
        I=I,
        b=b,
        a_cycling=a_cycling,
        z_cycling=z_cycling,
        E_cycling=E_cycling,
        R_gas=R_gas,
        T_kelvin=T_kelvin,
    )
    # note: your original had exp(z_cycling_knee*0) which is 1 at knee
    d_after = (
        (I / (3600.0 * 2.0 * b))
        * z_cycling_knee
        * c
        * np.exp(-E_cycling / (R_gas * T_kelvin))
        * 1.0
        / b
    )
    if d_after == 0:
        return c
    return c * (d_before / d_after)
