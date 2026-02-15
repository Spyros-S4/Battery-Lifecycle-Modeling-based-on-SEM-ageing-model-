# src/plots.py
import matplotlib.pyplot as plt
import pandas as pd


def plot_dqdt_weekly(df_weekly: pd.DataFrame):
    plt.figure(figsize=(10, 6))
    plt.plot(df_weekly["week"], df_weekly["dQdt"].abs(), marker="o", label="|dQ/dt|")
    plt.xlabel("Time (Weeks)")
    plt.ylabel("|dQ/dt|")
    plt.title("|dQ/dt| vs Time (weekly last sample)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_capacity_weekly(df_weekly: pd.DataFrame):
    plt.figure(figsize=(10, 6))
    plt.plot(df_weekly["week"], df_weekly["capacity_Ah"], marker="o", label="Capacity")
    plt.xlabel("Time (Weeks)")
    plt.ylabel("Capacity (Ah)")
    plt.title("Capacity vs Time (weekly last sample)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
