"""
STEP 5 — LSTM Battery RUL Training (all 7 batteries)
=====================================================
Uses Leave-One-Battery-Out (LOBO) cross-validation across
all 7 batteries: B0005, B0006, B0007, B0018, B0043, B0045, B0047.

Each round holds out one battery as the unseen test battery
and trains on the remaining 6. Results are averaged at the end.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping


# ================================================================
# PARAMETERS
# ================================================================

WINDOW_SIZE = 5     # 5 cycles of history to predict next RUL
                    # Larger now that we have more data per battery
EPOCHS      = 200
BATCH_SIZE  = 16    # Larger batch — more training data now
THRESHOLD   = 0.80


# ================================================================
# STEP 1 — LOAD ALL 7 BATTERIES
# ================================================================

files = {
    "B0005" : "nasa_classic/B0005_lstm_ready.csv",
    "B0006" : "nasa_classic/B0006_lstm_ready.csv",
    "B0007" : "nasa_classic/B0007_lstm_ready.csv",
    "B0018" : "nasa_classic/B0018_lstm_ready.csv",
    "B0043" : "nasa_classic/B0043_lstm_ready.csv",
    "B0045" : "nasa_classic/B0045_lstm_ready.csv",
    "B0047" : "nasa_classic/B0047_lstm_ready.csv",
}

batteries = {}
for name, path in files.items():
    df = pd.read_csv(path)
    df.sort_values("Cycle", inplace=True)
    df.reset_index(drop=True, inplace=True)
    batteries[name] = df
    print(f"  Loaded {name}: {df.shape}")


# ================================================================
# STEP 2 — RECOMPUTE RUL (per-battery 80% threshold)
# ================================================================
# Recomputed here so this script is self-contained, even if
# the CSVs already have a RUL column from Step 3.

def compute_rul(df, threshold_pct=THRESHOLD):
    df = df.copy()
    initial_cap   = df["DischargeCapacity_Ah"].iloc[:5].mean()
    eol_threshold = initial_cap * threshold_pct
    below         = df[df["DischargeCapacity_Ah"] < eol_threshold]
    eol_cycle     = below["Cycle"].iloc[0] if len(below) > 0 else df["Cycle"].max()
    df["RUL"]     = (eol_cycle - df["Cycle"]).clip(lower=0)
    return df

print("\nRUL ranges:")
for name in batteries:
    batteries[name] = compute_rul(batteries[name])
    df = batteries[name]
    nz = (df["RUL"] > 0).sum()
    print(f"  {name}: RUL {int(df['RUL'].min())}–{int(df['RUL'].max())} "
          f"| degrading rows: {nz}/{len(df)}")


# ================================================================
# STEP 3 — HANDLE NaN VALUES
# ================================================================
# Some batteries may have NaNs in impedance columns if data was
# missing. We fill with column median from the same battery —
# safe because impedance changes slowly across cycles.

FEATURE_COLS = [c for c in list(batteries.values())[0].columns
                if c not in ["RUL", "Cycle"]]

for name in batteries:
    before = batteries[name][FEATURE_COLS].isnull().sum().sum()
    batteries[name][FEATURE_COLS] = (
        batteries[name][FEATURE_COLS]
        .fillna(batteries[name][FEATURE_COLS].median())
    )
    after = batteries[name][FEATURE_COLS].isnull().sum().sum()
    if before > 0:
        print(f"  {name}: filled {before} NaNs → {after} remaining")


# ================================================================
# STEP 4 — SEQUENCE CREATION
# ================================================================

def create_sequences(X, y, window_size):
    """
    Sliding window: each sample is (window_size past cycles → next RUL).
    Input shape: (n_samples, window_size, n_features)
    """
    X_seq, y_seq = [], []
    for i in range(len(X) - window_size):
        X_seq.append(X[i : i + window_size])
        y_seq.append(y[i + window_size])
    return np.array(X_seq), np.array(y_seq)


def scale_and_window(df, feat_scaler, rul_scaler, window_size):
    """Scale a battery's data using pre-fitted scalers, then window it."""
    X = feat_scaler.transform(df[FEATURE_COLS].values)
    y = rul_scaler.transform(df["RUL"].values.reshape(-1, 1)).flatten()
    return create_sequences(X, y, window_size)


# ================================================================
# STEP 5 — MODEL BUILDER
# ================================================================
# Architecture with 7 batteries worth of data we can afford a
# slightly deeper model:
#   LSTM(64)   — captures temporal degradation trends
#   Dropout    — prevents overfitting (drops 20% of neurons randomly)
#   Dense(32)  — intermediate representation layer
#   Dense(1)   — final RUL prediction

def build_model(window_size, n_features):
    model = Sequential([
        LSTM(64, input_shape=(window_size, n_features),
             return_sequences=False),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


# ================================================================
# STEP 6 — LEAVE-ONE-BATTERY-OUT CROSS VALIDATION
# ================================================================
# 7 rounds, each holding out a different battery as the test set.
# This gives a robust estimate of how well the model generalises
# to batteries it has never seen during training.

all_results = {}
battery_names = list(batteries.keys())

n_rounds = len(battery_names)
fig, axes = plt.subplots(n_rounds, 2, figsize=(14, n_rounds * 3.5))
fig.suptitle("LSTM Battery RUL — Leave-One-Battery-Out (7 Batteries)",
             fontsize=13, fontweight="bold")

for round_idx, test_name in enumerate(battery_names):

    print(f"\n{'='*55}")
    print(f"  ROUND {round_idx+1}/{n_rounds}: Test = {test_name}")
    print(f"{'='*55}")

    test_df   = batteries[test_name]
    train_dfs = [batteries[n] for n in battery_names if n != test_name]

    # ── Fit scalers on training data only (no leakage) ──────────
    train_combined = pd.concat(train_dfs, ignore_index=True)

    feat_scaler = MinMaxScaler()
    feat_scaler.fit(train_combined[FEATURE_COLS].values)

    rul_scaler = MinMaxScaler()
    rul_scaler.fit(train_combined["RUL"].values.reshape(-1, 1))

    # ── Window each training battery separately ──────────────────
    X_train_list, y_train_list = [], []
    for df in train_dfs:
        Xs, ys = scale_and_window(df, feat_scaler, rul_scaler, WINDOW_SIZE)
        X_train_list.append(Xs)
        y_train_list.append(ys)

    X_train = np.concatenate(X_train_list, axis=0)
    y_train = np.concatenate(y_train_list, axis=0)

    # ── Window test battery ──────────────────────────────────────
    X_test, y_test = scale_and_window(
        test_df, feat_scaler, rul_scaler, WINDOW_SIZE)

    print(f"  Train sequences: {X_train.shape}")
    print(f"  Test  sequences: {X_test.shape}")

    # ── Train ────────────────────────────────────────────────────
    model = build_model(WINDOW_SIZE, X_train.shape[2])

    early_stop = EarlyStopping(
        monitor="val_loss",
        patience=20,
        restore_best_weights=True,
        verbose=0
    )

    history = model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_split=0.2,
        callbacks=[early_stop],
        verbose=0
    )
    print(f"  Stopped at epoch: {len(history.history['loss'])}")

    # ── Predict + inverse transform ──────────────────────────────
    pred_scaled = model.predict(X_test, verbose=0).flatten()
    pred_actual = np.clip(
        rul_scaler.inverse_transform(
            pred_scaled.reshape(-1, 1)).flatten(), 0, None)
    y_actual = rul_scaler.inverse_transform(
        y_test.reshape(-1, 1)).flatten()

    # ── Metrics ──────────────────────────────────────────────────
    r2   = r2_score(y_actual, pred_actual)
    mae  = mean_absolute_error(y_actual, pred_actual)
    rmse = np.sqrt(mean_squared_error(y_actual, pred_actual))
    all_results[test_name] = {"R2": r2, "MAE": mae, "RMSE": rmse}

    print(f"\n  R²   : {r2:.4f}")
    print(f"  MAE  : {mae:.4f} cycles")
    print(f"  RMSE : {rmse:.4f} cycles")

    # ── Plot ─────────────────────────────────────────────────────
    ax_loss = axes[round_idx, 0]
    ax_pred = axes[round_idx, 1]

    ax_loss.plot(history.history["loss"],     label="Train Loss")
    ax_loss.plot(history.history["val_loss"], label="Val Loss")
    ax_loss.set_title(f"Round {round_idx+1}: Loss (test={test_name})")
    ax_loss.set_xlabel("Epoch")
    ax_loss.set_ylabel("MSE (scaled)")
    ax_loss.legend(fontsize=8)
    ax_loss.grid(True, alpha=0.3)

    ax_pred.plot(y_actual,    label="Actual RUL",    linewidth=2)
    ax_pred.plot(pred_actual, label="Predicted RUL", linewidth=2,
                 linestyle="--")
    ax_pred.set_title(f"Round {round_idx+1}: {test_name} | "
                      f"R²={r2:.3f}  MAE={mae:.2f}")
    ax_pred.set_xlabel("Cycle Index")
    ax_pred.set_ylabel("RUL (cycles)")
    ax_pred.legend(fontsize=8)
    ax_pred.grid(True, alpha=0.3)


# ================================================================
# STEP 7 — FINAL SUMMARY
# ================================================================

print(f"\n{'='*55}")
print("  LOBO CROSS-VALIDATION SUMMARY (7 batteries)")
print(f"{'='*55}")
print(f"  {'Battery':<10} {'R²':>8} {'MAE':>10} {'RMSE':>10}")
print(f"  {'-'*42}")

r2_vals, mae_vals, rmse_vals = [], [], []
for name, res in all_results.items():
    print(f"  {name:<10} {res['R2']:>8.4f} "
          f"{res['MAE']:>10.4f} {res['RMSE']:>10.4f}")
    r2_vals.append(res["R2"])
    mae_vals.append(res["MAE"])
    rmse_vals.append(res["RMSE"])

print(f"  {'-'*42}")
print(f"  {'AVERAGE':<10} {np.mean(r2_vals):>8.4f} "
      f"{np.mean(mae_vals):>10.4f} {np.mean(rmse_vals):>10.4f}")

plt.tight_layout()
plt.savefig("lstm_7battery_results.png", dpi=150)
plt.show()
print("\nPlot saved as lstm_7battery_results.png")