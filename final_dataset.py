import pandas as pd

# Load previously saved CSV files
discharge_df = pd.read_csv("discharge_features.csv")
charge_df = pd.read_csv("charge_features.csv")
imp_df = pd.read_csv("impedance_features.csv")

# Merge discharge + charge
final_df = discharge_df.merge(charge_df, on="Cycle", how="left")

# Merge impedance
final_df = final_df.merge(imp_df, on="Cycle", how="left")

# Handle missing values (important)
final_df = final_df.ffill()

# Sort by cycle
final_df = final_df.sort_values("Cycle").reset_index(drop=True)

print(final_df.head())
print("\nFinal dataset shape:", final_df.shape)

# Save final dataset
# final_df.to_csv("battery_final_dataset.csv", index=False)

print(final_df.isna().sum())

# SOH calculation
initial_capacity = final_df["DischargeCapacity_Ah"].iloc[0]

final_df["SOH"] = final_df["DischargeCapacity_Ah"] / initial_capacity

# RUL calculation
EOL_threshold = 0.8 * initial_capacity

eol_cycle = final_df[final_df["DischargeCapacity_Ah"] <= EOL_threshold]["Cycle"].iloc[0]

final_df["RUL"] = eol_cycle - final_df["Cycle"]
final_df["RUL"] = final_df["RUL"].clip(lower=0)

print("\nWith SOH and RUL:")
print(final_df[["Cycle", "DischargeCapacity_Ah", "SOH", "RUL"]].head(10))

final_df.to_csv("battery_final_dataset_clean.csv", index=False)
print("\n final dataset saved successfully.")