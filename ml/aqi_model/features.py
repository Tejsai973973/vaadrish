import numpy as np
import pandas as pd
from math import radians, sin, cos, sqrt, atan2


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in km between two lat/lon coordinates."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (sin(dlat / 2) ** 2
         + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2)
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def compute_fire_features(
    station_lat: float,
    station_lon: float,
    fire_df: pd.DataFrame,
    date: pd.Timestamp,
    lookback_days: int = 3,
) -> dict:
    """
    Compute fire proximity features for a given station and date.
    Looks back `lookback_days` to capture smoke transport lag.
    """
    mask = (
        (fire_df["date"] >= date - pd.Timedelta(days=lookback_days))
        & (fire_df["date"] <= date)
    )
    nearby = fire_df[mask].copy()

    if nearby.empty:
        return {
            "fire_count_50":  0,
            "fire_count_100": 0,
            "fire_count_200": 0,
            "avg_frp_50":     0.0,
            "avg_frp_100":    0.0,
            "max_frp":        0.0,
            "weighted_frp":   0.0,
        }

    nearby["dist_km"] = nearby.apply(
        lambda r: haversine(station_lat, station_lon, r["lat"], r["lon"]),
        axis=1,
    )

    f50  = nearby[nearby["dist_km"] <= 50]
    f100 = nearby[nearby["dist_km"] <= 100]
    f200 = nearby[nearby["dist_km"] <= 200]
    f300 = nearby[nearby["dist_km"] <= 300]

    weighted_frp = 0.0
    if not f300.empty:
        w = 1.0 / (f300["dist_km"] + 1.0)
        weighted_frp = float((f300["frp"] * w).sum() / w.sum())

    return {
        "fire_count_50":  int(len(f50)),
        "fire_count_100": int(len(f100)),
        "fire_count_200": int(len(f200)),
        "avg_frp_50":     float(f50["frp"].mean())  if not f50.empty  else 0.0,
        "avg_frp_100":    float(f100["frp"].mean()) if not f100.empty else 0.0,
        "max_frp":        float(f200["frp"].max())  if not f200.empty else 0.0,
        "weighted_frp":   weighted_frp,
    }


def build_feature_matrix(
    aqi_df: pd.DataFrame,
    fire_df: pd.DataFrame,
    seq_len: int = 7,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build (X, y) arrays for training.

    X shape: (n_samples, seq_len, n_features)
    y shape: (n_samples,)

    For each city, we create a sliding window of `seq_len` days
    and predict the AQI on the next day.
    """
    FEATURE_COLS = [
        "fire_count_50", "fire_count_100", "fire_count_200",
        "avg_frp_50", "avg_frp_100", "max_frp", "weighted_frp",
        "pm25", "no2", "so2", "co", "o3",
        "month_sin", "month_cos", "day_norm",
    ]

    all_X, all_y = [], []
    fire_df = fire_df.copy()
    fire_df["date"] = pd.to_datetime(fire_df["date"])

    for city, group in aqi_df.groupby("city"):
        group = group.sort_values("date").reset_index(drop=True)
        if len(group) < seq_len + 1:
            continue

        city_lat = float(group["lat"].iloc[0])
        city_lon = float(group["lon"].iloc[0])

        rows = []
        for _, row in group.iterrows():
            ff = compute_fire_features(
                city_lat, city_lon, fire_df,
                pd.Timestamp(row["date"])
            )
            month     = pd.Timestamp(row["date"]).month
            day_norm  = pd.Timestamp(row["date"]).timetuple().tm_yday / 365.0
            feat = {
                **ff,
                "pm25":      float(row.get("pm25", 0) or 0),
                "no2":       float(row.get("no2",  0) or 0),
                "so2":       float(row.get("so2",  0) or 0),
                "co":        float(row.get("co",   0) or 0),
                "o3":        float(row.get("o3",   0) or 0),
                "month_sin": float(np.sin(2 * np.pi * month / 12)),
                "month_cos": float(np.cos(2 * np.pi * month / 12)),
                "day_norm":  day_norm,
            }
            rows.append(feat)

        feat_arr = np.array([[r[c] for c in FEATURE_COLS] for r in rows],
                            dtype=np.float32)
        aqi_arr  = group["aqi"].values.astype(np.float32)

        for i in range(len(feat_arr) - seq_len):
            all_X.append(feat_arr[i : i + seq_len])
            all_y.append(aqi_arr[i + seq_len])

    return np.array(all_X, dtype=np.float32), np.array(all_y, dtype=np.float32)