"""
ERA5-Land Meteorological Data Pipeline via Google Earth Engine.

Uses ECMWF/ERA5_LAND/DAILY_AGGR (1950–present, ~9km resolution)
NOT ERA5/DAILY which stopped at July 2020.

Fetches daily surface meteorological parameters for 20 Indian cities:
  - 2m air temperature (K → °C)
  - Relative humidity (derived from dewpoint via Magnus formula)
  - 10m U and V wind components → wind speed and direction
  - Surface pressure (Pa → hPa)
  - Total precipitation (m/day → mm/day)
"""

import ee
import math
import pandas as pd
from pathlib import Path
from loguru import logger

from api.core.config import get_settings

settings  = get_settings()
INDIA_BOX = [68.0, 6.0, 97.0, 36.0]
DATA_DIR  = Path("data/raw/gee")
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATIONS = [
    ("Delhi",      28.6139, 77.2090),
    ("Mumbai",     19.0760, 72.8777),
    ("Kolkata",    22.5726, 88.3639),
    ("Chennai",    13.0827, 80.2707),
    ("Bengaluru",  12.9716, 77.5946),
    ("Hyderabad",  17.3850, 78.4867),
    ("Ahmedabad",  23.0225, 72.5714),
    ("Lucknow",    26.8467, 80.9462),
    ("Kanpur",     26.4499, 80.3319),
    ("Patna",      25.5941, 85.1376),
    ("Varanasi",   25.3176, 82.9739),
    ("Agra",       27.1767, 78.0081),
    ("Jaipur",     26.9124, 75.7873),
    ("Noida",      28.5355, 77.3910),
    ("Gurgaon",    28.4595, 77.0266),
    ("Faridabad",  28.4089, 77.3178),
    ("Ghaziabad",  28.6692, 77.4538),
    ("Chandigarh", 30.7333, 76.7794),
    ("Bhopal",     23.2599, 77.4126),
    ("Nagpur",     21.1458, 79.0882),
]

# ERA5-Land Daily Aggregated band names
# https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR
ERA5_BANDS = [
    "temperature_2m",          # K
    "dewpoint_temperature_2m", # K
    "u_component_of_wind_10m", # m/s
    "v_component_of_wind_10m", # m/s
    "surface_pressure",        # Pa
    "total_precipitation_sum", # m/day
]


def init_gee() -> None:
    ee.Initialize(project=settings.gee_project)
    logger.info(f"GEE initialized: {settings.gee_project}")


def _rh_from_dewpoint(temp_k: float, dewpoint_k: float) -> float:
    """Relative humidity via Magnus formula. Inputs in Kelvin."""
    temp_c = temp_k - 273.15
    dew_c  = dewpoint_k - 273.15
    rh = 100 * math.exp((17.625 * dew_c) / (243.04 + dew_c)) / \
               math.exp((17.625 * temp_c) / (243.04 + temp_c))
    return round(min(max(rh, 0), 100), 2)


def fetch_era5(start: str, end: str) -> pd.DataFrame:
    """
    Fetch ERA5-Land period-mean meteorological data for 20 Indian cities.

    Parameters
    ----------
    start, end : str  — YYYY-MM-DD date strings.

    Returns
    -------
    pd.DataFrame with columns:
        city, lat, lon, start_date, end_date,
        temp_c, rh_pct, wind_speed, wind_dir, pressure_hpa, precip_mm
    """
    init_gee()

    era5 = (
        ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
        .select(ERA5_BANDS)
        .filterDate(start, end)
        .mean()
        # reproject forces a known CRS so sampleRegions can locate pixels
        .reproject(crs="EPSG:4326", scale=11132)
    )

    points = ee.FeatureCollection([
        ee.Feature(
            ee.Geometry.Point([lon, lat]),
            {"city": city, "lat": lat, "lon": lon}
        )
        for city, lat, lon in STATIONS
    ])

    sampled = era5.sampleRegions(
        collection=points,
        scale=11132,   # ERA5-Land native ~9km (11132m at equator in degrees)
        geometries=True,
    )

    features = sampled.getInfo()["features"]
    rows = []
    for f in features:
        p = f["properties"]

        temp_k   = p.get("temperature_2m")
        dew_k    = p.get("dewpoint_temperature_2m")
        u_wind   = p.get("u_component_of_wind_10m") or 0.0
        v_wind   = p.get("v_component_of_wind_10m") or 0.0
        pressure = p.get("surface_pressure")
        precip   = p.get("total_precipitation_sum") or 0.0

        wind_speed = round(math.sqrt(u_wind**2 + v_wind**2), 3)
        wind_dir   = round((270 - math.degrees(math.atan2(v_wind, u_wind))) % 360, 1) \
                     if (u_wind or v_wind) else None
        temp_c     = round(temp_k - 273.15, 2) if temp_k is not None else None
        rh         = _rh_from_dewpoint(temp_k, dew_k) \
                     if (temp_k is not None and dew_k is not None) else None

        rows.append({
            "city":         p.get("city"),
            "lat":          p.get("lat"),
            "lon":          p.get("lon"),
            "start_date":   start,
            "end_date":     end,
            "temp_c":       temp_c,
            "rh_pct":       rh,
            "wind_speed":   wind_speed,
            "wind_dir":     wind_dir,
            "pressure_hpa": round(pressure / 100, 2) if pressure else None,
            "precip_mm":    round(precip * 1000, 3),
        })

    df = pd.DataFrame(rows)
    out_path = DATA_DIR / f"era5_{start}_{end}.csv"
    df.to_csv(out_path, index=False)
    logger.success(f"ERA5 data saved → {out_path} ({len(df)} stations)")
    return df


if __name__ == "__main__":
    df = fetch_era5("2024-10-01", "2024-11-30")
    print(df.to_string())
