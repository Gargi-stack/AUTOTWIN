import pandas as pd
import numpy as np
import glob
import os

folder_path = r"C:\Users\nashd\OneDrive\Desktop\AUTOTWIN_Dashboard\B0047-Charge"
all_files = glob.glob(folder_path + "/*.csv")

results = []

for file in all_files:
    df = pd.read_csv(file)

    # Convert Time column to seconds
    df['Time'] = pd.to_datetime(df['Time'])
    df['DeltaT'] = df['Time'].diff().dt.total_seconds()

    # Replace NaN for first row
    df['DeltaT'] = df['DeltaT'].fillna(0)

    # Capacity calculation
    # Current is in Amps, time in seconds → convert to Ah
    df['CapacityContribution'] = df['Current_measured'] * df['DeltaT'] / 3600

    cycle_capacity = df['CapacityContribution'].sum()

    results.append({
        "File": os.path.basename(file),
        "AvgVoltage": df['Voltage_measured'].mean(),
        "AvgCurrent": df['Current_measured'].mean(),
        "MaxTemp": df['Temperature_measured'].max(),
        "CycleCapacity_Ah": cycle_capacity
    })

# Final table
results_df = pd.DataFrame(results)
print(results_df)