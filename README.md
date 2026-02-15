# SEM v2 — Battery Degradation Simulation (Capacity + Resistance)

This script runs a simple time-stepped simulation of battery degradation and produces plots for:
- Capacity fade over time (weeks)
- Degradation rate proxy (`dQ/dt`) over time (weekly sampling)
- Resistance increase over time
- Calendar vs cycling contribution (capacity loss)
- Capacity (and SOH) vs Full Charge Equivalents (FCE)

## What it does
- Initializes battery and aging model parameters (capacity `b`, temperature `T`, SOC, DOD, activation energies, etc.).
- Simulates degradation in a cycling loop until a capacity-loss threshold is reached (`threshold`, in %).
- Tracks:
  - Capacity (Ah)
  - Capacity-loss percentage (`Q_percentage`)
  - Throughput → FCE
  - Resistance increase (%)
- Samples results at the end of each whole week and generates plots.

## Requirements
- Python 3.9+ (recommended)
- numpy
- pandas
- matplotlib

