import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping

# =====================================================
# PARAMETERS
# =====================================================

WINDOW_SIZE = 10
EPOCHS = 100
BATCH_SIZE = 8

# =====================================================
# 1️⃣ LOAD DATA
# =====================================================

b43 = pd.read_csv("B0043_lstm_ready.csv")
b47 = pd.read_csv("B0047_lstm_ready.csv")
b45 = pd.read_csv("B0045_lstm_ready.csv")

# Sort by cycle
for df in [b43, b47, b45]:
    df.sort_values("Cycle", inplace=True)
    df.reset_index(drop=True, inplace=True)

# =====================================================
# 2️⃣ TRAIN DATA (43 + 47)
# =====================================================

train_df = pd.concat([b43, b47], ignore_index=True)

# Separate features and target
X_train_df = train_df.drop(columns=["RUL"])
y_train_df = train_df["RUL"]

X_test_df = b45.drop(columns=["RUL"])
y_test_df = b45["RUL"]

# =====================================================
# 3️⃣ SCALING (VERY IMPORTANT)
# =====================================================

scaler = MinMaxScaler()

X_train_scaled = scaler.fit_transform(X_train_df)
X_test_scaled = scaler.transform(X_test_df)

# =====================================================
# 4️⃣ CREATE SLIDING WINDOWS
# =====================================================

def create_sequences(X, y, window_size):
    X_seq = []
    y_seq = []
    
    for i in range(len(X) - window_size):
        X_seq.append(X[i:i+window_size])
        y_seq.append(y.iloc[i+window_size])
        
    return np.array(X_seq), np.array(y_seq)

X_train_seq, y_train_seq = create_sequences(
    X_train_scaled, y_train_df, WINDOW_SIZE
)

X_test_seq, y_test_seq = create_sequences(
    X_test_scaled, y_test_df, WINDOW_SIZE
)

print("Train shape:", X_train_seq.shape)
print("Test shape:", X_test_seq.shape)

# =====================================================
# 5️⃣ BUILD LSTM MODEL
# =====================================================

model = Sequential()
model.add(LSTM(64, input_shape=(WINDOW_SIZE, X_train_seq.shape[2])))
model.add(Dense(1))

model.compile(
    optimizer="adam",
    loss="mse"
)

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=10,
    restore_best_weights=True
)

# =====================================================
# 6️⃣ TRAIN
# =====================================================

history = model.fit(
    X_train_seq,
    y_train_seq,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_split=0.2,
    callbacks=[early_stop],
    verbose=1
)

# =====================================================
# 7️⃣ TEST ON UNSEEN BATTERY 46
# =====================================================

pred = model.predict(X_test_seq).flatten()

print("\n===== LSTM Unseen Battery 45 =====")
print("R2   :", r2_score(y_test_seq, pred))
print("MAE  :", mean_absolute_error(y_test_seq, pred))
print("RMSE :", np.sqrt(mean_squared_error(y_test_seq, pred)))

# =====================================================
# 8️⃣ PLOT RESULTS
# =====================================================

plt.figure(figsize=(10,5))
plt.plot(y_test_seq, label="Actual RUL")
plt.plot(pred, label="Predicted RUL")
plt.title("LSTM - Battery 46 Unseen Validation")
plt.xlabel("Cycle Index")
plt.ylabel("RUL")
plt.legend()
plt.show()