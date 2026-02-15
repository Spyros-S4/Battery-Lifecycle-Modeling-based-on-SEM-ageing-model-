# src/postprocess.py
import pandas as pd
import numpy as np


def weekly_last_sample(df: pd.DataFrame) -> pd.DataFrame:
    # week index = floor(t_week)
    wk = np.floor(df["t_week"].to_numpy()).astype(int)
    df2 = df.copy()
    df2["week"] = wk
    # keep last row of each week
    out = df2.sort_values("t_s").groupby("week", as_index=False).tail(1)
    return out.reset_index(drop=True)
