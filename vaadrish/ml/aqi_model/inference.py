"""
ONNX inference wrapper for the AQI CNN-LSTM model.
Used by the FastAPI model router to serve predictions.
"""

from pathlib import Path
import numpy as np
import joblib
import onnxruntime as ort

MODELS_DIR = Path("data/models")

_session:   ort.InferenceSession | None = None
_scaler_X   = None
_scaler_y   = None
SEQ_LEN     = 7
N_FEATURES  = 15


def load_model() -> None:
    global _session, _scaler_X, _scaler_y
    onnx_path = MODELS_DIR / "aqi_cnn_lstm.onnx"
    if not onnx_path.exists():
        raise FileNotFoundError(
            f"ONNX model not found at {onnx_path}. "
            "Run ml/aqi_model/train.py first."
        )
    _session = ort.InferenceSession(str(onnx_path),
                                    providers=["CPUExecutionProvider"])
    _scaler_X = joblib.load(MODELS_DIR / "scaler_X.pkl")
    _scaler_y = joblib.load(MODELS_DIR / "scaler_y.pkl")


def predict_aqi(feature_sequence: np.ndarray) -> float:
    """
    Predict AQI from a feature sequence.

    Args:
        feature_sequence: shape (SEQ_LEN, N_FEATURES)

    Returns:
        Predicted AQI as float.
    """
    global _session, _scaler_X, _scaler_y

    if _session is None:
        load_model()

    x = feature_sequence.reshape(-1, N_FEATURES)
    x = _scaler_X.transform(x).reshape(1, SEQ_LEN, N_FEATURES).astype(np.float32)

    raw = _session.run(["aqi"], {"features": x})[0]
    aqi = _scaler_y.inverse_transform(raw.reshape(-1, 1)).ravel()[0]
    return float(np.clip(aqi, 0, 500))