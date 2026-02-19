import pandas as pd
import numpy as np
import glob
import os

folder_path = r"C:\Users\gargi\Desktop\COURCE\final year project\B0047- Battery 47\discharge"
all_files = glob.glob(folder_path + "/*.csv")

results = []

for file in all_files:
    df = pd.read_csv(file)

    # Ensure sorted by Time (important)
    df = df.sort_values("Time")

    # Time difference (already in seconds)
    df["DeltaT"] = df["Time"].diff().fillna(0)

    # Capacity calculation (Current in Amps, Time in seconds)
    df["CapacityContribution"] = abs(df["Current_measured"]) * df["DeltaT"] / 3600

    cycle_capacity = df["CapacityContribution"].sum()

    results.append({
        "File": os.path.basename(file),
        "AvgVoltage": df["Voltage_measured"].mean(),
        "MinVoltage": df["Voltage_measured"].min(),
        "AvgCurrent": df["Current_measured"].mean(),
        "MaxTemp": df["Temperature_measured"].max(),
        "DischargeCapacity_Ah": cycle_capacity
    })

# Create final DataFrame
results_df = pd.DataFrame(results)

# Sort correctly by file name
results_df = results_df.sort_values("File").reset_index(drop=True)

# Add cycle number
results_df["Cycle"] = range(1, len(results_df) + 1)

print(results_df)

# print(results_df[results_df["Cycle"]==18])

# defining EOL
initial_capacity = results_df["DischargeCapacity_Ah"].iloc[0]
EOL_threshold = 0.8 * initial_capacity

print("Initial Capacity:", initial_capacity)
print("EOL Threshold (80%):", EOL_threshold)

# EOL cycle is the first cycle where capacity falls below threshold
EOL_cycle = results_df[
    results_df["DischargeCapacity_Ah"] <= EOL_threshold
]["Cycle"].iloc[0]

print("\n EOL occurs at cycle:", EOL_cycle)

# creating RUL 
results_df["RUL"] = EOL_cycle - results_df["Cycle"]

print(results_df[["Cycle", "DischargeCapacity_Ah", "RUL"]].head(20))

results_df.to_csv("discharge_features.csv", index=False)
print("Discharge features saved.")





