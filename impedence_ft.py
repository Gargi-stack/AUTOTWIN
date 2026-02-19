import pandas as pd
import glob
import os
import numpy as np

folder_path = r"C:\Users\gargi\Desktop\COURCE\final year project\B0047- Battery 47\impedance"
all_files = glob.glob(folder_path + "/*.csv")

results = []

for file in all_files:
    df = pd.read_csv(file)

    # List of complex columns
    complex_cols = [
        "Sense_current",
        "Battery_current",
        "Current_ratio",
        "Battery_impedance",
        "Rectified_Impedance"
    ]

    # Convert all to complex and compute magnitude
    for col in complex_cols:
        df[col] = df[col].apply(lambda x: complex(x))
        df[col + "_mag"] = np.abs(df[col])

    results.append({
        "File": os.path.basename(file),
        "Avg_Battery_Impedance": df["Battery_impedance_mag"].mean(),
        "Max_Battery_Impedance": df["Battery_impedance_mag"].max(),
        "Avg_Rectified_Impedance": df["Rectified_Impedance_mag"].mean(),
        "Avg_Current_Ratio": df["Current_ratio_mag"].mean(),
        "Avg_Sense_Current": df["Sense_current_mag"].mean(),
        "Avg_Battery_Current": df["Battery_current_mag"].mean()
    })

imp_df = pd.DataFrame(results)

imp_df = imp_df.sort_values("File").reset_index(drop=True)
imp_df["Cycle"] = range(1, len(imp_df) + 1)

print(imp_df)

imp_df.to_csv("impedance_features.csv", index=False)
print("Impedance features saved.")

