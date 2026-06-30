"""
Training script for Vaadrish AQI prediction model.
Trains CNN-LSTM + Attention and XGBoost ensemble, exports CNN-LSTM to ONNX.

Run from project root:
    python ml/aqi_model/train.py
"""

import asyncio
import os
import json
import sys
from pathlib import Path

import asyncpg
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ml.aqi_model.features import build_feature_matrix
from ml.aqi_model.model import CNNLSTMAttention

load_dotenv()

MODELS_DIR = Path("data/models")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

SEQ_LEN    = 7
N_FEATURES = 15
EPOCHS     = 60
BATCH_SIZE = 64
LR         = 1e-3
DEVICE     = torch.device("cuda" if torch.cuda.is_available() else "cpu")


async def load_data_from_db() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_url = os.getenv("DATABASE_URL", "")
    asyncpg_url = raw_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(asyncpg_url)

    aqi_records = await conn.fetch("""
        SELECT
            ar.date,
            ar.aqi_actual         AS aqi,
            ar.pm25_actual        AS pm25,
            ar.no2, ar.so2, ar.co, ar.o3,
            ST_X(s.location::geometry) AS lon,
            ST_Y(s.location::geometry) AS lat,
            s.city
        FROM aqi_readings ar
        JOIN stations s ON ar.station_id = s.id
        WHERE ar.aqi_actual > 0
        ORDER BY ar.date, s.city
    """)

    fire_records = await conn.fetch("""
        SELECT
            date,
            frp,
            ST_X(location::geometry) AS lon,
            ST_Y(location::geometry) AS lat
        FROM fire_events
        ORDER BY date
    """)

    await conn.close()

    aqi_df  = pd.DataFrame([dict(r) for r in aqi_records])
    fire_df = pd.DataFrame([dict(r) for r in fire_records])

    print(f"Loaded {len(aqi_df)} AQI readings and {len(fire_df)} fire events")
    return aqi_df, fire_df


def train_cnn_lstm(X: np.ndarray, y: np.ndarray) -> tuple:
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()

    X_flat = X.reshape(-1, N_FEATURES)
    X_flat = scaler_X.fit_transform(X_flat)
    X      = X_flat.reshape(-1, SEQ_LEN, N_FEATURES)
    y_s    = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

    X_t = torch.tensor(X,   dtype=torch.float32)
    y_t = torch.tensor(y_s, dtype=torch.float32)

    dataset = TensorDataset(X_t, y_t)
    n_val   = max(1, int(0.2 * len(dataset)))
    n_train = len(dataset) - n_val
    train_ds, val_ds = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE)

    model     = CNNLSTMAttention(n_features=N_FEATURES).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    criterion = nn.HuberLoss()

    best_val_loss = float("inf")
    best_state    = None

    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item() * len(xb)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                val_loss += criterion(model(xb), yb).item() * len(xb)

        train_loss /= n_train
        val_loss   /= n_val
        scheduler.step()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state    = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if epoch % 10 == 0:
            print(f"  Epoch {epoch:3d}/{EPOCHS} | train={train_loss:.4f} | val={val_loss:.4f}")

    model.load_state_dict(best_state)
    return model, scaler_X, scaler_y



def evaluate(y_true: np.ndarray, y_pred: np.ndarray, name: str) -> dict:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))
    print(f"\n{name} results:")
    print(f"  RMSE : {rmse:.2f}")
    print(f"  MAE  : {mae:.2f}")
    print(f"  R2   : {r2:.4f}")
    return {"model": name, "rmse": rmse, "mae": mae, "r2": r2}



def export_onnx(model: nn.Module, scaler_X: StandardScaler) -> None:
    model.eval()
    dummy = torch.zeros(1, SEQ_LEN, N_FEATURES, dtype=torch.float32)
    path  = MODELS_DIR / "aqi_cnn_lstm.onnx"
    torch.onnx.export(
        model, dummy, str(path),
        input_names=["features"],
        output_names=["aqi"],
        dynamic_axes={"features": {0: "batch_size"}},
        opset_version=17,
    )
    print(f"\nONNX model saved to {path}")


async def main() -> None:
    print("Loading data from database...")
    aqi_df, fire_df = await load_data_from_db()

    print("\nBuilding feature matrix...")
    X, y = build_feature_matrix(aqi_df, fire_df, seq_len=SEQ_LEN)
    print(f"Dataset shape: X={X.shape}, y={y.shape}")

    if len(X) < 50:
        print("Not enough data. Run AQI ingest for more dates first.")
        return

    # Train/test split
    split     = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # CNN-LSTM 
    print(f"\nTraining CNN-LSTM on {DEVICE}...")
    model, scaler_X, scaler_y = train_cnn_lstm(X_train, y_train)

    model.eval()
    X_test_flat = scaler_X.transform(X_test.reshape(-1, N_FEATURES)).reshape(-1, SEQ_LEN, N_FEATURES)
    X_test_t    = torch.tensor(X_test_flat, dtype=torch.float32).to(DEVICE)
    with torch.no_grad():
        y_pred_s = model(X_test_t).cpu().numpy()
    y_pred_cnn = scaler_y.inverse_transform(y_pred_s.reshape(-1, 1)).ravel()
    cnn_metrics = evaluate(y_test, y_pred_cnn, "CNN-LSTM")

    # Save model and scalers
    torch.save(model.state_dict(), MODELS_DIR / "aqi_cnn_lstm.pt")
    joblib.dump(scaler_X, MODELS_DIR / "scaler_X.pkl")
    joblib.dump(scaler_y, MODELS_DIR / "scaler_y.pkl")
    export_onnx(model, scaler_X)

    #XGBoost 
    print("\nTraining XGBoost...")
    X_train_flat = X_train.reshape(len(X_train), -1)
    X_test_flat2 = X_test.reshape(len(X_test), -1)

    xgb_model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        tree_method="hist",
    )
    xgb_model.fit(X_train_flat, y_train,
                  eval_set=[(X_test_flat2, y_test)],
                  verbose=False)
    y_pred_xgb  = xgb_model.predict(X_test_flat2)
    xgb_metrics = evaluate(y_test, y_pred_xgb, "XGBoost")

    joblib.dump(xgb_model, MODELS_DIR / "aqi_xgboost.pkl")

    # Ensemble (average) 
    y_ensemble    = 0.5 * y_pred_cnn + 0.5 * y_pred_xgb
    ens_metrics   = evaluate(y_test, y_ensemble, "Ensemble (CNN-LSTM + XGBoost)")

    # Save metrics summary
    metrics = {
        "cnn_lstm":  cnn_metrics,
        "xgboost":   xgb_metrics,
        "ensemble":  ens_metrics,
    }
    with open(MODELS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nAll models saved to {MODELS_DIR}/")
    print("Training complete.")


if __name__ == "__main__":
    asyncio.run(main())