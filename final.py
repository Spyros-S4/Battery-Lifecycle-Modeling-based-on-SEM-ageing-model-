import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def calendar_degradation_rate(Q_pct, T, SOC, params):
    """
    Compute dQ/dt for calendar aging with safety guards.
    """
    z = params['z_calendar'](T)
    b = params['b_calendar'](SOC)
    E = params['E_calendar']
    R = params['R']

    if z == 0 or b <= 0 or Q_pct <= 0:
        return 0.0

    base = b * np.exp(-E / (R * T))
    if base <= 0:
        return 0.0

    ratio = Q_pct / base
    exponent = 1 - 1 / z
    if ratio == 0 and exponent < 0:
        return 0.0

    return (
        z
        * b
        * np.exp(-E / (R * T))
        * ratio ** exponent
        / 100
        / 604800
    )


def cycling_degradation_rate(FCE, T, SOC, DOD, I, b, params):
    """
    Compute dQ/dt for cycling aging depending on knee, with guards.
    """
    z = params['z_cycling'](T)
    a = params['a_cycling'](SOC, DOD)
    E = params['E_cycling']
    R = params['R']

    if b <= 0 or I <= 0:
        return 0.0

    if FCE < params['FCE_knee_threshold']:
        if FCE <= 0 or z == 0:
            return 0.0
        return (
            I / (3600 * b)
            * a
            * z
            * np.exp(-E / (R * T))
            * (FCE ** (z - 1))
            / b
        )
    else:
        z_k = params['z_cycling_knee'](T)
        c = params['c_cycling'](SOC, DOD)
        if z_k == 0:
            return 0.0
        return (
            I / (3600 * b)
            * z_k
            * c
            * np.exp(-E / (R * T))
            * np.exp(z_k * (FCE - params['FCE_knee_value']))
            / b
        )


def simulate(params):
    """
    Run combined calendar & cycling degradation simulation.
    Returns simulation history and summary metrics.
    """
    ts = []
    caps = []
    Qpcts = []
    dQdts = []
    dRdts = []

    time_step = params['time_step']
    b0 = params['initial_capacity']
    I = params['I']
    max_time = params['max_time']

    t = 0.0
    cap = b0
    Q_pct = 0.0
    throughput = 0.0

    while Q_pct < params['threshold_pct'] and t < max_time:
        FCE = throughput / b0
        cycle_phase = (t % (params['calendar_dur'] + params['cycling_dur']))

        if cycle_phase < params['calendar_dur']:
            dQdt = calendar_degradation_rate(Q_pct, params['T'], params['SOC'], params)
        else:
            dQdt = cycling_degradation_rate(FCE, params['T'], params['SOC'], params['DOD'], I, b0, params)
            throughput += I * time_step / 3600

        dRdt = params['resistance_factor'] * abs(dQdt)

        cap -= abs(dQdt) * time_step * b0
        Q_pct = max(0.0, (b0 - cap) / b0 * 100)

        ts.append(t)
        caps.append(cap)
        Qpcts.append(Q_pct)
        dQdts.append(dQdt)
        dRdts.append(dRdt)

        t += time_step

    # Summary metrics
    total_time_h = t / 3600
    total_throughput = throughput
    total_FCE = throughput / b0
    FCE_knee = params['FCE_knee_value']
    Q_critical = params.get('Q_critical', None)
    calendar_loss = sum([calendar_degradation_rate(q, params['T'], params['SOC'], params) * time_step * b0 for q in Qpcts])
    cycling_loss = sum([abs(cycling_degradation_rate(throughput/b0 if i>params['calendar_dur'] else 0,
                         params['T'], params['SOC'], params['DOD'], I, b0, params)
                         ) * time_step * b0 for i, throughput in enumerate([throughput]*len(Qpcts))])
    final_resistance = dRdts[-1] if dRdts else 0

    df = pd.DataFrame({
        'time_s': ts,
        'capacity': caps,
        'Q_pct': Qpcts,
        'dQdt': dQdts,
        'dRdt': dRdts
    })

    summary = {
        'total_time_h': total_time_h,
        'total_throughput_Ah': total_throughput,
        'total_FCE': total_FCE,
        'FCE_knee': FCE_knee,
        'Q_critical': Q_critical,
        'calendar_loss_Ah': calendar_loss,
        'cycling_loss_Ah': cycling_loss,
        'final_resistance_%': final_resistance
    }

    return df, summary


def plot_results(df, b0):
    df['week'] = df['time_s'] / (3600 * 24 * 7)

    plt.figure()
    plt.plot(df['week'], df['capacity'], label='Capacity')
    plt.axhline(b0 * 0.8, linestyle='--', label='80% of Initial')
    plt.xlabel('Weeks')
    plt.ylabel('Capacity (Ah)')
    plt.legend()
    plt.grid(True)
    plt.show()

    plt.figure()
    plt.plot(df['week'], np.abs(df['dQdt']), label='dQ/dt')
    plt.xlabel('Weeks')
    plt.ylabel('dQ/dt (Ah/s)')
    plt.legend()
    plt.grid(True)
    plt.show()

    plt.figure()
    plt.plot(df['week'], df['dRdt'], label='Resistance Increase %')
    plt.xlabel('Weeks')
    plt.ylabel('%')
    plt.legend()
    plt.grid(True)
    plt.show()


def main():
    params = {
        'threshold_pct': 20,
        'time_step': 20,
        'initial_capacity': 118.1993,
        'I': 113,
        'R': 8.314,
        'T': 273.15 + int(input("Enter temperature in Celcious :  ")),
        'SOC': 0.475,
        'DOD': 0.75,
        'E_calendar': 4.6368e4,
        'E_cycling': 2.9093e4,
        'calendar_dur': 1,
        'cycling_dur': 6000,
        'max_time': 1e7,
        'resistance_factor': 3.5,
        'Q_critical': 0.001,
        'FCE_knee_value': 0,
        'FCE_knee_threshold': 0.001,
        'z_calendar': lambda T: -7.79e-5 * T**2 + 0.04647 * T - 6.229,
        'b_calendar': lambda SOC: -7.7003e7 * SOC**2 + 1.1370e8 * SOC + 1.6926e6,
        'z_cycling': lambda T: (-0.1459 * T + 42.1416) if T <= 283.15 else (0.0017634 * T + 0.44027),
        'z_cycling_knee': lambda T: 1.8466e87 * T**(-36.7340),
        'a_cycling': lambda SOC, DOD: abs(-618.3836 + -1558.6554 * SOC + 765.6587 * DOD + 237.1955 * SOC * DOD),
        'c_cycling': lambda SOC, DOD: 2.9323e6 -1.6187e7 * SOC + 3.6801e6 * DOD -9.9384e3 * SOC * DOD,
    }

    df, summary = simulate(params)
    print(f"Total time run: {summary['total_time_h']:.2f} hours")
    print(f"Total throughput: {summary['total_throughput_Ah']:.2f} Ah")
    print(f"Total number of FCE cycles: {summary['total_FCE']:.2f}")
    print(f"FCE at knee point: {summary['FCE_knee']}")
    print(f"Critical Q% loss: {summary['Q_critical']}")
    print(f"Q loss calendar: {summary['calendar_loss_Ah']:.2f} Ah")
    print(f"Q loss cycling: {summary['cycling_loss_Ah']:.2f} Ah")
    print(f"Resistance has increase by: {summary['final_resistance_%']:.2f} %")

    plot_results(df, params['initial_capacity'])


if __name__ == '__main__':
    main()