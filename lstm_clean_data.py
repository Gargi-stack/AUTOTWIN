import pandas as pd

# Load file
df = pd.read_csv("B0045_clean.csv")

# Drop unnecessary columns
drop_cols = ["SOH", "File_x", "File_y", "File"]

df_clean = df.drop(columns=drop_cols, errors="ignore")

# Sort by Cycle (very important for LSTM)
df_clean = df_clean.sort_values("Cycle").reset_index(drop=True)

# Save cleaned file
df_clean.to_csv("B0045_lstm_ready.csv", index=False)

print("Cleaned shape:", df_clean.shape)
print("Columns now:")
print(df_clean.columns)