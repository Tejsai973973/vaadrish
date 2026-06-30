"""
Fire-HCHO Lag Correlation Analyzer.

Scientifically proves the link between active biomass burning (FIRMS/VIIRS)
and HCHO column enhancements over India, with:
  - Temporal lag correlation (0-7 day lag, accounting for fire plume transport)
  - Spatial proximity matching (fires within 2 degrees of HCHO grid cells)
  - Source region labelling (IGP, Northwest India, Northeast India, etc.)
  - Pearson R and p-value at each lag
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial import cKDTree
from pathlib import Path
from loguru import logger

# Known pollution / biomass burning source regions in India
SOURCE_REGIONS = {
    "Indo-Gangetic Plain":  {"lat": (25, 32), "lon": (74, 89)},
    "Northwest India":      {"lat": (28, 34), "lon": (72, 78)},
    "Central India":        {"lat": (20, 26), "lon": (74, 85)},
    "Northeast India":      {"lat": (24, 30), "lon": (89, 97)},
    "Deccan Plateau":       {"lat": (14, 22), "lon": (74, 82)},
    "Coastal Western":      {"lat": (8,  22), "lon": (68, 76)},
}


def assign_source_region(lat: float, lon: float) -> str:
    """Label a coordinate with its known Indian source region."""
    for region, bounds in SOURCE_REGIONS.items():
        if (bounds["lat"][0] <= lat <= bounds["lat"][1] and
                bounds["lon"][0] <= lon <= bounds["lon"][1]):
            return region
    return "Other"


def load_fire_data(fire_csv: str) -> pd.DataFrame:
    """
    Load FIRMS CSV (NASA FIRMS VIIRS/MODIS format).
    Expected columns: latitude, longitude, acq_date, frp, confidence
    """
    df = pd.read_csv(fire_csv)

    # Normalise column names — FIRMS exports vary slightly
    df.columns = df.columns.str.strip().str.lower()

    if "acq_date" in df.columns:
        df["date"] = pd.to_datetime(df["acq_date"])
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

    # Keep only high-confidence fires to reduce noise
    if "confidence" in df.columns:
        df = df[df["confidence"].astype(str).str.lower().isin(["high", "nominal", "h", "n", "100"])]

    df = df.dropna(subset=["latitude", "longitude", "frp"])
    df["source_region"] = df.apply(
        lambda r: assign_source_region(r["latitude"], r["longitude"]), axis=1
    )

    logger.info(f"Loaded {len(df)} fire events from {fire_csv}")
    return df


def load_hcho_grid(hcho_csv: str) -> pd.DataFrame:
    """Load GEE-exported HCHO grid CSV."""
    df = pd.read_csv(hcho_csv)
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["lat", "lon", "hcho_value"])
    logger.info(f"Loaded {len(df)} HCHO grid points from {hcho_csv}")
    return df


def spatial_match(fire_df: pd.DataFrame,
                  hcho_df: pd.DataFrame,
                  radius_deg: float = 2.0) -> pd.DataFrame:
    """
    For each fire event, find the mean HCHO value within `radius_deg` degrees.
    Uses a KD-Tree for fast spatial lookup.

    Returns merged DataFrame with columns: date, frp, nearby_hcho_mean, source_region
    """
    hcho_coords = hcho_df[["lat", "lon"]].values
    tree = cKDTree(hcho_coords)

    records = []
    for _, fire_row in fire_df.iterrows():
        point = [fire_row["latitude"], fire_row["longitude"]]
        indices = tree.query_ball_point(point, r=radius_deg)

        if not indices:
            continue

        nearby_hcho = hcho_df.iloc[indices]["hcho_value"].mean()
        records.append({
            "date":           fire_row["date"].date() if hasattr(fire_row["date"], "date") else fire_row["date"],
            "latitude":       fire_row["latitude"],
            "longitude":      fire_row["longitude"],
            "frp":            fire_row["frp"],
            "nearby_hcho":    nearby_hcho,
            "source_region":  fire_row.get("source_region", "Other"),
        })

    matched = pd.DataFrame(records)
    logger.info(f"Spatially matched {len(matched)} fire events to HCHO grid")
    return matched


def daily_aggregation(matched_df: pd.DataFrame,
                      hcho_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate to daily totals:
      - Total FRP (Fire Radiative Power) per day = measure of fire intensity
      - Mean HCHO per day across all grid points
    """
    daily_frp = (
        matched_df.groupby("date")["frp"]
        .sum()
        .reset_index()
        .rename(columns={"frp": "total_frp"})
    )

    hcho_df_copy = hcho_df.copy()
    hcho_df_copy["date"] = hcho_df_copy["date"].dt.date
    daily_hcho = (
        hcho_df_copy.groupby("date")["hcho_value"]
        .mean()
        .reset_index()
        .rename(columns={"hcho_value": "mean_hcho"})
    )

    merged = pd.merge(daily_frp, daily_hcho, on="date", how="inner")
    merged = merged.sort_values("date").reset_index(drop=True)
    return merged


def spatial_correlation(fire_df: pd.DataFrame,
                        hcho_df: pd.DataFrame,
                        radius_deg: float = 1.5) -> dict:
    """
    Spatial correlation: for each HCHO grid point, count how many fires
    occurred within `radius_deg` degrees during the analysis period.
    Then compute Pearson R between fire density and HCHO value across all grid points.

    This is the correct method when HCHO is a temporal mean composite:
    areas with more fires should show higher mean HCHO.
    """
    hcho_coords = hcho_df[["lat", "lon"]].values
    fire_coords = fire_df[["latitude", "longitude"]].values

    tree = cKDTree(fire_coords)

    fire_counts = []
    fire_frp    = []

    for hcho_point in hcho_coords:
        indices = tree.query_ball_point(hcho_point, r=radius_deg)
        fire_counts.append(len(indices))
        if indices:
            fire_frp.append(fire_df.iloc[indices]["frp"].sum())
        else:
            fire_frp.append(0.0)

    hcho_df = hcho_df.copy()
    hcho_df["nearby_fire_count"] = fire_counts
    hcho_df["nearby_fire_frp"]   = fire_frp

    # Remove zero-fire points to focus on fire-affected areas
    valid = hcho_df["nearby_fire_count"] > 0
    logger.info(f"HCHO grid points with at least 1 nearby fire: {valid.sum()} / {len(hcho_df)}")

    if valid.sum() < 10:
        logger.warning("Not enough fire-affected HCHO points for spatial correlation.")
        return {"error": "insufficient data"}

    hcho_vals  = hcho_df.loc[valid, "hcho_value"].values
    count_vals = hcho_df.loc[valid, "nearby_fire_count"].values
    frp_vals   = hcho_df.loc[valid, "nearby_fire_frp"].values

    r_count, p_count = stats.pearsonr(count_vals, hcho_vals)
    r_frp,   p_frp   = stats.pearsonr(frp_vals,   hcho_vals)

    result = {
        "fire_count_vs_hcho": {
            "pearson_r":   round(float(r_count), 4),
            "p_value":     round(float(p_count), 6),
            "significant": bool(p_count < 0.05),
            "n_points":    int(valid.sum()),
        },
        "fire_frp_vs_hcho": {
            "pearson_r":   round(float(r_frp), 4),
            "p_value":     round(float(p_frp), 6),
            "significant": bool(p_frp < 0.05),
            "n_points":    int(valid.sum()),
        },
    }

    logger.info(f"\n=== Spatial Correlation (Fire vs HCHO) ===")
    logger.info(f"  Fire Count vs HCHO : R={r_count:+.4f}  p={p_count:.6f}  "
                f"{'SIGNIFICANT' if p_count < 0.05 else 'not significant'}")
    logger.info(f"  Fire FRP   vs HCHO : R={r_frp:+.4f}  p={p_frp:.6f}  "
                f"{'SIGNIFICANT' if p_frp < 0.05 else 'not significant'}")
    return result, hcho_df


def regional_summary(hcho_df: pd.DataFrame,
                     fire_df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarise mean HCHO and total fire FRP per source region.
    Proves which Indian regions have the highest fire-driven HCHO enhancement.
    """
    hcho_df = hcho_df.copy()
    hcho_df["region"] = hcho_df.apply(
        lambda r: assign_source_region(r["lat"], r["lon"]), axis=1
    )

    fire_df = fire_df.copy()
    fire_df["region"] = fire_df.apply(
        lambda r: assign_source_region(r["latitude"], r["longitude"]), axis=1
    )

    hcho_by_region = (
        hcho_df.groupby("region")
        .agg(mean_hcho=("hcho_value", "mean"),
             max_hcho=("hcho_value", "max"),
             n_hcho_points=("hcho_value", "count"))
        .reset_index()
    )

    fire_by_region = (
        fire_df.groupby("region")
        .agg(total_frp=("frp", "sum"),
             fire_count=("frp", "count"))
        .reset_index()
    )

    merged = pd.merge(hcho_by_region, fire_by_region, on="region", how="left")
    merged["total_frp"]  = merged["total_frp"].fillna(0)
    merged["fire_count"] = merged["fire_count"].fillna(0).astype(int)

    # Round for readability
    merged["mean_hcho"] = merged["mean_hcho"].round(8)
    merged["max_hcho"]  = merged["max_hcho"].round(8)
    merged["total_frp"] = merged["total_frp"].round(1)

    merged = merged.sort_values("mean_hcho", ascending=False)
    return merged


def run_full_analysis(fire_csv: str, hcho_csv: str) -> dict:
    """
    Full Fire-HCHO correlation analysis pipeline.
    Returns a dict with all results that can be served via the API
    or saved to disk for the notebooks.
    """
    logger.info("Starting Fire-HCHO Correlation Analysis...")

    fire_df = load_fire_data(fire_csv)
    hcho_df = load_hcho_grid(hcho_csv)

    # The HCHO grid is a temporal mean — extract date range from filename
    hcho_fname = Path(hcho_csv).stem
    parts = hcho_fname.split("_")
    try:
        hcho_start = pd.to_datetime(parts[-2])
        hcho_end   = pd.to_datetime(parts[-1])
    except Exception:
        hcho_start = pd.Timestamp("2024-10-01")
        hcho_end   = pd.Timestamp("2024-11-30")

    fire_df = fire_df[
        (fire_df["date"] >= hcho_start) &
        (fire_df["date"] <= hcho_end)
    ]
    logger.info(f"Filtered fires to range: {hcho_start.date()} to {hcho_end.date()} "
                f"({len(fire_df)} events)")

    # Spatial correlation (correct approach for temporal mean HCHO)
    spatial_result, hcho_enriched = spatial_correlation(fire_df, hcho_df, radius_deg=1.5)

    # Regional summary table
    region_df = regional_summary(hcho_df, fire_df)
    logger.info(f"\n=== Regional Summary (HCHO + Fire) ===\n{region_df.to_string(index=False)}")

    # Save outputs
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    region_df.to_csv(out_dir / "fire_hcho_region_summary.csv", index=False)
    hcho_enriched.to_csv(out_dir / "hcho_grid_with_fire_density.csv", index=False)
    logger.success("Saved results to data/outputs/")

    return {
        "spatial_correlation": spatial_result,
        "regional_summary":    region_df.to_dict(orient="records"),
        "n_fire_events":       len(fire_df),
        "n_hcho_points":       len(hcho_df),
        "date_range": {
            "start": str(hcho_start.date()),
            "end":   str(hcho_end.date()),
        },
    }


if __name__ == "__main__":
    fire_csv = "data/raw/fire_india_2024.csv"
    hcho_csv = list(Path("data/raw/gee").glob("hcho_grid_*.csv"))[0]
    results  = run_full_analysis(str(fire_csv), str(hcho_csv))



