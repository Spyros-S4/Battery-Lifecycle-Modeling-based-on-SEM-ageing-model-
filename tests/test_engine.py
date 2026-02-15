# tests/test_engine.py
from src.engine import Params, run_simulation

def test_engine_stops_and_capacity_decreases():
    p = Params(
        threshold=1.0,
        time_step=1000.0,
        T_kelvin=298.15,
        I=100.0,
        b=100.0,
        calendar_duration=10000.0,
        cycling_duration=10000.0,
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
        Q_critical=0.5,
        c_init=1.0,
        resistance_scale_cycling=1.0,
    )
    df = run_simulation(p)
    assert len(df) > 5
    assert df["Q_loss_pct"].iloc[-1] >= p.threshold
    assert df["capacity_Ah"].iloc[-1] <= df["capacity_Ah"].iloc[0]
