"""
HYBRID DIGITAL TWIN — LSTM + ECM (Residual Learning)
====================================================
LSTM learns ECM errors (Residual), not full RUL.

Final Prediction:
    Final_RUL = ECM_RUL + LSTM_predicted_residual
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import tensorflow as tf

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.get_logger().setLevel("ERROR")


# ================================================================
# PARAMETERS
# ================================================================

WINDOW_SIZE = 10
EPOCHS      = 300
BATCH_SIZE  = 16


# ================================================================
# LOAD DATA (HYBRID FILES)
# ================================================================

FILES = {
    "B0005": "nasa_classic/B0005_hybrid.csv",
    "B0006": "nasa_classic/B0006_hybrid.csv",
    "B0007": "nasa_classic/B0007_hybrid.csv",
    "B0018": "nasa_classic/B0018_hybrid.csv",
}

batteries = {}
print("Loading hybrid datasets...")

for name, path in FILES.items():
    df = pd.read_csv(path)
    df.sort_values("Cycle", inplace=True)
    df.reset_index(drop=True, inplace=True)
    batteries[name] = df
    print(f"  {name}: {len(df)} cycles loaded")


# ================================================================
# FEATURE SELECTION (INCLUDING ECM FEATURES)
# ================================================================

FEATURE_COLS = [
    "AvgVoltage_x",
    "MinVoltage",
    "AvgCurrent_x",
    "MaxTemp_x",
    "DischargeCapacity_Ah",
    "Avg_Battery_Impedance",
    "Max_Battery_Impedance",
    "Avg_Rectified_Impedance",
    "Avg_Current_Ratio",
    "Avg_Sense_Current",
    "Avg_Battery_Current",
    "R0",
    "R1",
    "C1",
    "tau"
]

print(f"\nFeatures used ({len(FEATURE_COLS)}): {FEATURE_COLS}")

for name in batteries:
    batteries[name][FEATURE_COLS] = (
        batteries[name][FEATURE_COLS]
        .fillna(batteries[name][FEATURE_COLS].median())
    )


# ================================================================
# SEQUENCE CREATION
# ================================================================

def create_sequences(X, y, window_size):
    X_seq, y_seq = [], []
    for i in range(len(X) - window_size):
        X_seq.append(X[i : i + window_size])
        y_seq.append(y[i + window_size])
    return np.array(X_seq), np.array(y_seq)


# ================================================================
# MODEL
# ================================================================

def build_model(window_size, n_features):
    model = Sequential([
        LSTM(64, input_shape=(window_size, n_features)),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


# ================================================================
# LOBO CROSS VALIDATION
# ================================================================

battery_names = list(batteries.keys())
all_results   = {}

fig, axes = plt.subplots(4, 1, figsize=(10, 20))
fig.suptitle("HYBRID MODEL — ECM + LSTM (Residual Learning)", fontsize=14)

for idx, test_name in enumerate(battery_names):

    print(f"\n{'='*55}")
    print(f"TEST BATTERY: {test_name}")
    print(f"{'='*55}")

    test_df   = batteries[test_name].copy()
    train_dfs = [batteries[n].copy() for n in battery_names if n != test_name]

    # ---------------------------
    # SCALE FEATURES
    # ---------------------------
    train_combined = pd.concat(train_dfs, ignore_index=True)
    scaler = MinMaxScaler()
    scaler.fit(train_combined[FEATURE_COLS])

    # ---------------------------
    # CREATE TRAIN DATA
    # ---------------------------
    X_train_list, y_train_list = [], []

    for df in train_dfs:
        X_scaled = scaler.transform(df[FEATURE_COLS])
        y = df["Residual"].values   # ⭐ TARGET = Residual

        X_seq, y_seq = create_sequences(X_scaled, y, WINDOW_SIZE)
        X_train_list.append(X_seq)
        y_train_list.append(y_seq)

    X_train = np.concatenate(X_train_list)
    y_train = np.concatenate(y_train_list)

    # ---------------------------
    # TEST DATA
    # ---------------------------
    X_test_scaled = scaler.transform(test_df[FEATURE_COLS])
    y_actual = test_df["RUL"].values[WINDOW_SIZE:]

    X_test, _ = create_sequences(
        X_test_scaled,
        test_df["Residual"].values,
        WINDOW_SIZE
    )

    print(f"Train shape: {X_train.shape}")
    print(f"Test shape : {X_test.shape}")

    # ---------------------------
    # TRAIN MODEL
    # ---------------------------
    model = build_model(WINDOW_SIZE, X_train.shape[2])

    early_stop = EarlyStopping(
        monitor="val_loss",
        patience=25,
        restore_best_weights=True
    )

    history = model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_split=0.2,
        callbacks=[early_stop],
        verbose=0
    )

    print(f"Stopped at epoch: {len(history.history['loss'])}")

    # ---------------------------
    # PREDICTION (HYBRID CORE)
    # ---------------------------
    pred_residual = model.predict(X_test, verbose=0).flatten()

    ecm_part = test_df["ECM_RUL"].values[WINDOW_SIZE:]

    final_rul = ecm_part + pred_residual   # ⭐ HYBRID OUTPUT

    # ---------------------------
    # METRICS
    # ---------------------------
    r2   = r2_score(y_actual, final_rul)
    mae  = mean_absolute_error(y_actual, final_rul)
    rmse = np.sqrt(mean_squared_error(y_actual, final_rul))

    all_results[test_name] = {"R2": r2, "MAE": mae, "RMSE": rmse}

    print(f"R2   : {r2:.4f}")
    print(f"MAE  : {mae:.2f}")
    print(f"RMSE : {rmse:.2f}")

    # ---------------------------
    # PLOT
    # ---------------------------
    ax = axes[idx]
    ax.plot(y_actual, label="Actual RUL", linewidth=2)
    ax.plot(final_rul, label="Hybrid Prediction", linestyle="--")
    ax.set_title(f"{test_name} | R2={r2:.3f}")
    ax.legend()
    ax.grid(True)


# ================================================================
# FINAL SUMMARY
# ================================================================

print(f"\n{'='*55}")
print("FINAL HYBRID RESULTS")
print(f"{'='*55}")

r2_list, mae_list, rmse_list = [], [], []

for name, res in all_results.items():
    print(f"{name} → R2={res['R2']:.4f}, MAE={res['MAE']:.2f}, RMSE={res['RMSE']:.2f}")
    r2_list.append(res["R2"])
    mae_list.append(res["MAE"])
    rmse_list.append(res["RMSE"])

print(f"\nAVERAGE R2   : {np.mean(r2_list):.4f}")
print(f"AVERAGE MAE  : {np.mean(mae_list):.2f}")
print(f"AVERAGE RMSE : {np.mean(rmse_list):.2f}")

plt.tight_layout()
plt.savefig("hybrid_results.png", dpi=150)
plt.show()