from sem.engine import Params, run_simulation
from sem.plots import plot_capacity_weekly, plot_dqdt_weekly
from sem.postprocess import weekly_last_sample

def main():

    p = Params(
        threshold=20.0,
        time_step=3600.0,
        T_kelvin=298.15,
        I=100.0,
        b=100.0,
        calendar_duration=7 * 24 * 3600,
        cycling_duration=7 * 24 * 3600,
        R_gas=8.314,
        z_calendar=1.2,
        b_calendar=1.0,
        E_calendar=20000.0,
        z_resistance=1.1,
        b_resistance=1.0,
        E_resistance=15000.0,
        a_cycling=1.0,
        z_cycling=1.1,
        z_cycling_knee=0.05,
        E_cycling=20000.0,
        Q_critical=5.0,
        c_init=1.0,
        resistance_scale_cycling=1.0,
    )

    df = run_simulation(p)

    df_weekly = weekly_last_sample(df)

    plot_capacity_weekly(df_weekly)
    plot_dqdt_weekly(df_weekly)


if __name__ == "__main__":
    main()
