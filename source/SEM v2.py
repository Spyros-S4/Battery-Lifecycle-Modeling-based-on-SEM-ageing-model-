import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

################ Simulation Parameters ##################################

threshold = 20  # degradation threshold

# Simulation settings
time_step = 10  # Time step in seconds

a = 1  # parameter for control
T = 20  # Temperature in C
T = T + 273.15  # Temperature in Kelvin
I = 113  # Discharge current in Ampere

I_discharge = I / 3  # C/3 [A]
I_charge = I * 1  # 1C [A]

R = 8.314  # Gas constant in J/(mol·K)
b = 118.1993  # Initial battery capacity (Ah)
SOC = 0.475  # used for calendar ageing
DOD = 0.75  # Depth of discharge
ratio = 1  # ratio between discharge and charge time

# cycling parameters
E_cycling = 2.909338197235501e04  # Activation energy for cycling in J/mol

a1 = -6.183836129704323e02
a2 = -1.558655355341110e03
a3 = 7.656586569744725e02
a4 = 2.371955481448591e02
a_cycling = abs(a1 + a2 * SOC + a3 * DOD + a4 * (SOC * DOD))

z11 = -0.145890455456764
z12 = 42.141599660720324
z21 = 0.001763435880793
z22 = 0.440267252758658

# Determine z based on the temperature
if T <= (10 + 273.15):
    z_cycling = z11 * T + z12
else:
    z_cycling = z21 * T + z22

# Knee Point based on Temperature parameters

Q1_T = 0.031182862984560
Q2_T = -17.291844113259910
Q3_T = 2.393313906474544e03

Q1_SOC = 37.356898628573740
Q2_SOC = -42.206581001423146
Q3_SOC = 23.401161303343933

SOC_factor = 0.475
k_factor = 1 / (Q1_SOC * SOC_factor**2 + Q2_SOC * SOC_factor + Q3_SOC)

Q_critical = (
    k_factor
    * (Q1_T * T**2 + Q2_T * T + Q3_T)
    * (Q1_SOC * SOC**2 + Q2_SOC * SOC + Q3_SOC)
)

if Q_critical <= 0:
    Q_critical = 0.01
    Q_percentage = 0.001
else:
    Q_percentage = 0.001

c1 = 2.932342965720117e06
c2 = -1.618716744215181e07
c3 = 3.680136148823878e06
c4 = -9.938364395543002e03
c = c1 + c2 * SOC + c3 * DOD + c4 * (SOC * DOD)

d1 = 1.846571482544108e87
d2 = -36.734006202685514
z_cycling_knee = d1 * T**d2

in_cycling_phase = False  # initialize the variable

# calendar ageing parameters
a11 = -6.884935816298182e-05
a12 = 0.040536672723914
a13 = -5.273064576795150
b11 = -8.079419666957326e08
b12 = 1.193092669085474e09
b13 = 1.779309209122286e07

z_calendar = a11 * T**2 + a12 * T + a13  # Calendar aging coefficient
b_calendar = b11 * SOC**2 + b12 * SOC + b13
E_calendar = 5.211157802748527e04  # Activation energy for calendar aging in J/mol

# Resistance Increase parameters

E_resistance = 4.636802465290228e04
a21 = -2.358827083634676e-05
a22 = 0.014315799859979
a23 = -1.427615803449020
b21 = -1.420603123621393e08
b22 = 2.263106081717418e08
b23 = 1.359869993501577e07

z_resistance = a21 * T**2 + a22 * T + a23
b_resistance = b21 * SOC**2 + b22 * SOC + b23

# Phases duration
calendar_duration = 0  # Calendar aging duration in seconds
cycling_duration = 3600 * 10  # Cycling aging duration in seconds

# Initialize variables for simulation
capacities = [b]  # Initial capacity list
capacity = b  # Current capacity
time_points = [0]  # Start time at 0 seconds
current_time = 0  # Initialize current time
dQdt_values = [0]  # Store dQdt values
dRdt_values = [0]  # Store dRdt values %
N_cycles = [0]  # store N cycles values
Q_per = [0]
dQ_dt_cyclingg = [0]
total_throughput = 0.1  # Total throughput (Ah) during cycling
cycling_throughput = 0.1  # Throughput for the current cycling phase
FCE_knee = 0.1
N = 0
Q_loss_calendar = 0
Q_loss_cycling = 0.05
R_percentage = 0.01
dRdt_cycling = 0
dRdt_calendar = 0
Resistance_scale_cycling = 1
dQ_dt_cycling = 0

# Run the simulation until a 20% capacity drop is observed
while Q_percentage < threshold:

    # Calculate cycles (FCE) and append
    FCE = total_throughput / b  # Full Charge Equivalents
    N_cycles.append(FCE)  # Append N cycles

    # Check if we are in a calendar aging event
    if current_time % (calendar_duration + cycling_duration) < calendar_duration:
        # Calendar aging phase
        in_cycling_phase = False
        dQdt = (
            z_calendar
            * b_calendar
            * np.exp(-E_calendar / (R * T))
            * (Q_percentage / (b_calendar * np.exp(-E_calendar / (R * T))))
            ** (1 - 1 / z_calendar)
            / 100
            / 604800  # Convert to weekly degradation rate
        )
        Q_loss_calendar += dQdt * time_step * b
        # Resistance increase calculation
        # Resistance Increase calculation
        dRdt_calendar = (
            z_resistance
            * b_resistance
            * np.exp(-E_resistance / (R * T))
            * (R_percentage / (b_resistance * np.exp(-E_resistance / (R * T))))
            ** (1 - 1 / z_resistance)
            / 100
            / 604800
            # Convert to weekly degradation rate
        )
    else:
        # Cycling degradation phase
        in_cycling_phase = True  # SET THE FLAG!

        if Q_percentage < Q_critical:
            # Calculate time from Q
            t_from_Q = (3600 * 2 * b / I) * (
                (b * (Q_percentage / 100)) / (a_cycling * np.exp(-E_cycling / (R * T)))
            ) ** (1 / z_cycling)

            # Calculate dQdt with factor of 2 (7200 = 2 * 3600)
            dQdt = (
                (I / (3600 * 2 * b))
                * a_cycling
                * z_cycling
                * np.exp(-E_cycling / (R * T))
                * ((I * t_from_Q) / (3600 * b)) ** (z_cycling - 1)
                / b
            )

            throughput_at_knee = total_throughput
            FCE_knee = throughput_at_knee / b

        else:
            # Detect knee point
            if a == 2:
                FCE_knee = total_throughput / b

                # Calculate dQdt_before at knee point
                dQdt_before_knee = (
                    (I / (3600 * 2 * b))
                    * a_cycling
                    * z_cycling
                    * np.exp(-E_cycling / (R * T))
                    * (FCE_knee ** (z_cycling - 1))
                    / b
                )

                # Calculate dQdt_after at knee point
                dQdt_after_knee = (
                    (I / (3600 * 2 * b))
                    * z_cycling_knee
                    * c
                    * np.exp(-E_cycling / (R * T))
                    * np.exp(z_cycling_knee * 0)
                    / b
                )

                # Adjust c to match continuity
                c = c * (dQdt_before_knee / dQdt_after_knee)
                a = 1

            # Post-knee degradation
            dQdt = (
                (I / (3600 * 2 * b))
                * z_cycling_knee
                * c
                * np.exp(-E_cycling / (R * T))
                * np.exp(z_cycling_knee * (FCE - FCE_knee))
                / b
            )

        Q_loss_cycling += abs(dQdt) * time_step * b

        # Resistance Increase calculation
        dRdt_cycling = (
            z_resistance
            * b_resistance
            * np.exp(-E_resistance / (R * T))
            * (R_percentage / (b_resistance * np.exp(-E_resistance / (R * T))))
            ** (1 - 1 / z_resistance)
            / 100
            / 604800
        )

        # Accumulate throughput during cycling
        # Divide by 2 because we accumulate during both charge and discharge,
        # but the model was fitted with FCE counting only discharge
        total_throughput += I * time_step / 3600 * 0.5

    # Update capacity and time (OUTSIDE the if/else blocks)
    capacity = capacity - abs(dQdt) * b * time_step

    R_percentage += (
        dRdt_calendar * time_step * 100
        + dRdt_cycling * time_step * 100 * Resistance_scale_cycling
    )

    if current_time > 0:
        Q_percentage = (b - capacity) / b * 100

    # Append updated values to lists
    dRdt_values.append(R_percentage)
    capacities.append(capacity)
    dQdt_values.append(abs(dQdt))
    current_time += time_step
    time_points.append(current_time)
# Output results
total_time_hours = current_time / 3600
print(f"Total time run: {current_time} seconds (~{total_time_hours:.2f} hours)")
print(f"Total throughput during cycling: {total_throughput:.2f} Ah")

# Convert time points from seconds to weeks
time_points_weeks = np.array(time_points) / (3600 * 24 * 7)  # Convert seconds to weeks
resistance_increase = np.array(dRdt_values)
dQ_dt_cyclingg = np.array(dQ_dt_cyclingg)

# Filter the data for whole weeks and capacity at the end of each week
filtered_data = []
for week in range(0, int(np.floor(time_points_weeks[-1])) + 1):  # Include week 0
    indices = np.where(np.floor(time_points_weeks) == week)[0]
    if len(indices) > 0:
        last_index = indices[-1]
        filtered_data.append((week, capacities[last_index], dQdt_values[last_index]))

# Create a DataFrame for filtered data
filtered_df = pd.DataFrame(filtered_data, columns=["Weeks", "Capacity (Ah)", "dQ_dt"])

print(f"Total number of FCE cycles: {N_cycles[-1]}")
print(f"FCE at knee point: {FCE_knee}")
print(f"Total number of FCE: {N_cycles[-1]}")
print(f"Critical Q% loss: {Q_critical}")
print(f"Q loss calendar: {Q_loss_calendar} Ah")
print(f"Q loss cycling: {Q_loss_cycling} Ah")
print(f"Resistance has increase by: {dRdt_values[-1]} %")

# Define a consistent capacity threshold (80% of initial/nominal capacity)
# If b is your nominal/initial capacity (Ah), keep this:
cap_threshold = b * (100 - threshold) / 100
# If you prefer using the first measured capacity instead, use this instead:
# cap_threshold = filtered_df["Capacity (Ah)"].iloc[0] * 0.8

# 1) dQ_dt vs Weeks (filtered)

plt.figure(figsize=(10, 6))
plt.plot(
    filtered_df["Weeks"].to_numpy(),
    filtered_df["dQ_dt"].abs().to_numpy(),
    label="|dQ/dt| (Filtered)",
    marker="o",
)
plt.xlabel("Time (Weeks)")
plt.ylabel("|dQ/dt| (Ah/week)")  # adjust if your unit differs
plt.title("|dQ/dt| vs Time (Filtered)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 2) Capacity vs Weeks (filtered)

plt.figure(figsize=(10, 6))
plt.plot(
    filtered_df["Weeks"].to_numpy(),
    filtered_df["Capacity (Ah)"].to_numpy(),
    label="Capacity (Ah)",
    marker="o",
)
plt.xlabel("Time (Weeks)")
plt.ylabel("Capacity (Ah)")
plt.title("Battery Capacity Over Time (Filtered)")
plt.axhline(cap_threshold, color="red", linestyle="--", label="80% Capacity Threshold")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 3) Capacity vs Weeks (model/sim arrays)

plt.figure(figsize=(10, 6))
plt.plot(
    np.asarray(time_points_weeks),
    np.asarray(capacities),
    label="Capacity (Ah)",
)
plt.xlabel("Time (Weeks)")
plt.ylabel("Capacity (Ah)")
plt.title("Battery Capacity Over Time (Cycling + Calendar Aging)")
plt.axhline(cap_threshold, color="red", linestyle="--", label="80% Capacity Threshold")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 4) Resistance increase vs Weeks

plt.figure(figsize=(10, 6))
plt.plot(
    np.asarray(time_points_weeks),
    np.asarray(resistance_increase),
    label="Resistance Increase (%)",
)
plt.xlabel("Time (Weeks)")
plt.ylabel("Resistance Increase (%)")
plt.title("Resistance Increase Over Time")
# Optional threshold for resistance (example: +20%). Change/remove as needed.
# plt.axhline(20, color="red", linestyle="--", label="+20% Resistance Threshold")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 5) Calendar vs Cycling contribution (same units!)

labels = ["Calendar Aging", "Cycling Aging"]
values = [Q_loss_calendar, Q_loss_cycling]

plt.figure(figsize=(10, 6))
plt.bar(labels, values)
plt.xlabel("Degradation Phase")
plt.ylabel(
    "Capacity Loss (same unit for both bars)"
)  # make sure both are Ah or both are %
plt.title("Calendar vs Cycling Aging Contributions")
plt.ylim(0, max(values) * 1.1 if max(values) != 0 else 1)
plt.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()

# 6) Capacity vs FCE

plt.figure(figsize=(10, 6))
plt.plot(
    np.asarray(N_cycles),
    np.asarray(capacities),
    label="Capacity (Ah)",
)
plt.xlabel("Full Charge Equivalents (FCE)")
plt.ylabel("Capacity (Ah)")
plt.title("Battery Capacity vs Full Cycles Equivalents (FCE)")
plt.axhline(cap_threshold, color="red", linestyle="--", label="80% Capacity Threshold")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 6) SOHs FCE

plt.figure(figsize=(10, 6))
plt.plot(
    np.asarray(N_cycles),
    np.asarray(capacities) / b * 100,
    label="Capacity (Ah)",
)
plt.xlabel("Full Charge Equivalents (FCE)")
plt.ylabel("State of Health (%)")
plt.title("Battery SOH Evolution vs Full Cycles Equivalents (FCE)")
plt.axhline(100-threshold, color="red", linestyle="--", label="80% Capacity Threshold")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
