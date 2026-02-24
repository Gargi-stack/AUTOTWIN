import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, max_error

# ─────────────────────────────────────────────────────────
# STEP 1: Load Data
# ─────────────────────────────────────────────────────────
b43 = pd.read_csv("B0043_clean.csv")
b47 = pd.read_csv("B0047_clean.csv")
b45 = pd.read_csv("B0045_clean.csv")

b43["Battery"] = "B0043"
b47["Battery"] = "B0047"
b45["Battery"] = "B0045"

# ─────────────────────────────────────────────────────────
# STEP 2: FIX 1 — Add Delta / Rate Features (per battery)
# ─────────────────────────────────────────────────────────
def add_delta_features(df):
    df = df.sort_values("Cycle").reset_index(drop=True)
    df["Capacity_lag1"]       = df["DischargeCapacity_Ah"].shift(1)
    df["Capacity_delta"]      = df["DischargeCapacity_Ah"].diff()
    df["Impedance_delta"]     = df["Avg_Battery_Impedance"].diff()
    df["Capacity_rollmean3"]  = df["DischargeCapacity_Ah"].rolling(3).mean()
    df["Impedance_rollmean3"] = df["Avg_Battery_Impedance"].rolling(3).mean()
    df = df.dropna().reset_index(drop=True)
    return df

b43 = add_delta_features(b43)
b47 = add_delta_features(b47)
b45 = add_delta_features(b45)

# ─────────────────────────────────────────────────────────
# STEP 3: Define Features and Target
# ─────────────────────────────────────────────────────────
FEATURES = [
    "AvgVoltage_x", "MinVoltage", "AvgCurrent_x", "MaxTemp_x",
    "DischargeCapacity_Ah",
    "AvgVoltage_y", "AvgCurrent_y", "MaxTemp_y",
    "CycleCapacity_Ah",
    "Avg_Battery_Impedance", "Max_Battery_Impedance",
    "Avg_Rectified_Impedance", "Avg_Current_Ratio",
    "Avg_Sense_Current", "Avg_Battery_Current",
    "Cycle",
    "Capacity_lag1", "Capacity_delta", "Impedance_delta",
    "Capacity_rollmean3", "Impedance_rollmean3",
]

TARGET = "SOH"

# ─────────────────────────────────────────────────────────
# STEP 4: Combine Train Batteries & Train/Test Split
# ─────────────────────────────────────────────────────────
train_val_df = pd.concat([b43, b47], ignore_index=True)

X = train_val_df[FEATURES]
y = train_val_df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=True
)

# ─────────────────────────────────────────────────────────
# STEP 5: FIX 3 — B0045 Early Cycle Adaptation Split
# ─────────────────────────────────────────────────────────
ADAPT_CYCLES = 10

b45_adapt   = b45[b45["Cycle"] <= ADAPT_CYCLES]
b45_holdout = b45[b45["Cycle"] >  ADAPT_CYCLES].reset_index(drop=True)

print(f"Train size        : {len(X_train)}")
print(f"Test size         : {len(X_test)}")
print(f"B0045 adapt size  : {len(b45_adapt)}  (first {ADAPT_CYCLES} cycles)")
print(f"B0045 holdout size: {len(b45_holdout)}  (unseen cycles)")

# ─────────────────────────────────────────────────────────
# STEP 6: FIX 2 — MinMax Scaling
# ─────────────────────────────────────────────────────────
scaler = MinMaxScaler()

X_train_scaled  = scaler.fit_transform(X_train)
X_test_scaled   = scaler.transform(X_test)
X_val_scaled    = scaler.transform(b45_holdout[FEATURES])
X_adapt_scaled  = scaler.transform(b45_adapt[FEATURES])

# Fine-tuned set = train + B0045 first 10 cycles
X_finetune = np.vstack([X_train_scaled, X_adapt_scaled])
y_finetune = pd.concat([y_train, b45_adapt[TARGET]]).reset_index(drop=True)

# ─────────────────────────────────────────────────────────
# STEP 7: Evaluation Function
# ─────────────────────────────────────────────────────────
def evaluate(y_true, y_pred, split_name):
    mae     = mean_absolute_error(y_true, y_pred)
    rmse    = np.sqrt(mean_squared_error(y_true, y_pred))
    r2      = r2_score(y_true, y_pred)
    max_err = max_error(y_true, y_pred)
    print(f"\n{'='*45}")
    print(f"  {split_name}")
    print(f"{'='*45}")
    print(f"  MAE       : {mae:.4f}")
    print(f"  RMSE      : {rmse:.4f}")
    print(f"  R²        : {r2:.4f}")
    print(f"  Max Error : {max_err:.4f}")
    return {"MAE": mae, "RMSE": rmse, "R2": r2, "MaxErr": max_err}

# ─────────────────────────────────────────────────────────
# STEP 8: MODEL A — XGBoost (No Fine-Tuning)
# ─────────────────────────────────────────────────────────
print("\n" + "="*50)
print("  MODEL A: XGBoost — No Fine-Tuning")
print("="*50)

xgb_base = XGBRegressor(
    n_estimators=300, learning_rate=0.05, max_depth=4,
    subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.1, reg_lambda=1.0,
    random_state=42, early_stopping_rounds=30,
    eval_metric="rmse", n_jobs=-1
)
xgb_base.fit(
    X_train_scaled, y_train,
    eval_set=[(X_test_scaled, y_test)],
    verbose=50
)

metrics_xgb_test = evaluate(y_test,              xgb_base.predict(X_test_scaled), "XGBoost — TEST SET")
metrics_xgb_val  = evaluate(b45_holdout[TARGET], xgb_base.predict(X_val_scaled),  "XGBoost — B0045 VALIDATION (no adapt)")
y_pred_xgb_val   = xgb_base.predict(X_val_scaled)

# ─────────────────────────────────────────────────────────
# STEP 9: MODEL B — XGBoost (With Fine-Tuning)
# ─────────────────────────────────────────────────────────
print("\n" + "="*50)
print("  MODEL B: XGBoost — With Fine-Tuning")
print("="*50)

xgb_ft = XGBRegressor(
    n_estimators=300, learning_rate=0.05, max_depth=4,
    subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.1, reg_lambda=1.0,
    random_state=42, early_stopping_rounds=30,
    eval_metric="rmse", n_jobs=-1
)
xgb_ft.fit(
    X_finetune, y_finetune,
    eval_set=[(X_test_scaled, y_test)],
    verbose=50
)

metrics_xgb_ft_test = evaluate(y_test,              xgb_ft.predict(X_test_scaled), "XGBoost FT — TEST SET")
metrics_xgb_ft_val  = evaluate(b45_holdout[TARGET], xgb_ft.predict(X_val_scaled),  "XGBoost FT — B0045 VALIDATION (with adapt)")
y_pred_xgb_ft_val   = xgb_ft.predict(X_val_scaled)

# ─────────────────────────────────────────────────────────
# STEP 10: Comparison Table
# ─────────────────────────────────────────────────────────
print("\n" + "="*65)
print("  MODEL COMPARISON SUMMARY")
print("="*65)
print(f"{'Model':<35} {'MAE':>8} {'RMSE':>8} {'R²':>8} {'MaxErr':>10}")
print("-"*65)

rows = [
    ("XGBoost (no adapt) — Test",   metrics_xgb_test),
    ("XGBoost (no adapt) — B0045",  metrics_xgb_val),
    ("XGBoost (w/ adapt) — Test",   metrics_xgb_ft_test),
    ("XGBoost (w/ adapt) — B0045",  metrics_xgb_ft_val),
]
for name, m in rows:
    print(f"{name:<35} {m['MAE']:>8.4f} {m['RMSE']:>8.4f} {m['R2']:>8.4f} {m['MaxErr']:>10.4f}")

# ─────────────────────────────────────────────────────────
# STEP 11: Degradation Plots — Side by Side
# ─────────────────────────────────────────────────────────
cycles_val = b45_holdout["Cycle"].values
actual_val = b45_holdout[TARGET].values

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

def plot_degradation(ax, cycles, actual, predicted, title):
    ax.plot(cycles, actual,    label="Actual SOH",    marker='o', ms=4)
    ax.plot(cycles, predicted, label="Predicted SOH", marker='x', ms=4)
    ax.set_xlabel("Cycle")
    ax.set_ylabel("SOH")
    ax.set_title(title)
    ax.legend()
    ax.grid(True)

plot_degradation(axes[0], cycles_val, actual_val, y_pred_xgb_val,
                 f"XGBoost — No Adapt\nB0045 Validation")

plot_degradation(axes[1], cycles_val, actual_val, y_pred_xgb_ft_val,
                 f"XGBoost — With Adapt ({ADAPT_CYCLES} cycles)\nB0045 Validation")

plt.suptitle("XGBoost SOH Prediction on Unseen Battery B0045", fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig("xgb_comparison_b0045.png", dpi=150)
plt.show()

# ─────────────────────────────────────────────────────────
# STEP 12: Feature Importance (Fine-Tuned Model)
# ─────────────────────────────────────────────────────────
feat_imp = pd.Series(xgb_ft.feature_importances_, index=FEATURES).sort_values(ascending=False)
plt.figure(figsize=(10, 5))
feat_imp.plot(kind='bar', color='steelblue')
plt.title("XGBoost Feature Importances (Fine-Tuned Model)")
plt.ylabel("Importance Score")
plt.tight_layout()
plt.savefig("feature_importance.png", dpi=150)
plt.show()

print("\nTop 5 features:")
print(feat_imp.head().to_string())