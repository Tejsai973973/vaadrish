"""
Fetches Sentinel-5P TROPOMI data (HCHO, NO2, SO2, CO, O3) for India
from Google Earth Engine and exports to CSV.
"""

import ee
import pandas as pd
from pathlib import Path
from loguru import logger
from datetime import date

from api.core.config import get_settings

settings  = get_settings()
INDIA_BOX = [68.0, 6.0, 97.0, 36.0]  # [west, south, east, north]
DATA_DIR  = Path("data/raw/gee")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# CPCB station coordinates for sampling
STATIONS = [
    ("Delhi",         28.6139,  77.2090),
    ("Mumbai",        19.0760,  72.8777),
    ("Kolkata",       22.5726,  88.3639),
    ("Chennai",       13.0827,  80.2707),
    ("Bengaluru",     12.9716,  77.5946),
    ("Hyderabad",     17.3850,  78.4867),
    ("Ahmedabad",     23.0225,  72.5714),
    ("Lucknow",       26.8467,  80.9462),
    ("Kanpur",        26.4499,  80.3319),
    ("Patna",         25.5941,  85.1376),
    ("Varanasi",      25.3176,  82.9739),
    ("Agra",          27.1767,  78.0081),
    ("Jaipur",        26.9124,  75.7873),
    ("Noida",         28.5355,  77.3910),
    ("Gurgaon",       28.4595,  77.0266),
    ("Faridabad",     28.4089,  77.3178),
    ("Ghaziabad",     28.6692,  77.4538),
    ("Chandigarh",    30.7333,  76.7794),
    ("Bhopal",        23.2599,  77.4126),
    ("Nagpur",        21.1458,  79.0882),
]


def init_gee() -> None:
    """Initialize GEE with project credentials."""
    ee.Initialize(project=settings.gee_project)
    logger.info(f"GEE initialized with project: {settings.gee_project}")


def fetch_hcho(start: str, end: str) -> pd.DataFrame:
    """
    Fetch Sentinel-5P TROPOMI HCHO column data for India.
    Returns DataFrame with lat, lon, hcho_value, date columns.
    """
    init_gee()
    geometry = ee.Geometry.Rectangle(INDIA_BOX)

    collection = (
        ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_HCHO")
        .select("tropospheric_HCHO_column_number_density")
        .filterDate(start, end)
        .filterBounds(geometry)
    )

    mean_img = collection.mean().clip(geometry)

    # Sample at CPCB station locations
    points = ee.FeatureCollection([
        ee.Feature(ee.Geometry.Point([lon, lat]), {"city": city, "lat": lat, "lon": lon})
        for city, lat, lon in STATIONS
    ])

    sampled = mean_img.sampleRegions(
        collection=points,
        scale=3500,
        geometries=True,
    )

    features = sampled.getInfo()["features"]
    rows = []
    for f in features:
        props = f["properties"]
        rows.append({
            "city":       props.get("city"),
            "lat":        props.get("lat"),
            "lon":        props.get("lon"),
            "hcho_value": props.get("tropospheric_HCHO_column_number_density", 0),
            "start_date": start,
            "end_date":   end,
        })

    df = pd.DataFrame(rows)
    logger.success(f"Fetched HCHO for {len(df)} stations ({start} to {end})")
    return df


def fetch_multi_pollutant(start: str, end: str) -> pd.DataFrame:
    """
    Fetch NO2, SO2, CO, O3 column data for India from Sentinel-5P.
    Returns merged DataFrame sampled at CPCB station locations.
    """
    init_gee()
    geometry = ee.Geometry.Rectangle(INDIA_BOX)

    datasets = {
        "NO2": ("COPERNICUS/S5P/OFFL/L3_NO2",  "tropospheric_NO2_column_number_density"),
        "SO2": ("COPERNICUS/S5P/OFFL/L3_SO2",  "SO2_column_number_density"),
        "CO":  ("COPERNICUS/S5P/OFFL/L3_CO",   "CO_column_number_density"),
        "O3":  ("COPERNICUS/S5P/OFFL/L3_O3",   "O3_column_number_density"),
    }

    images = {}
    for pollutant, (collection_id, band) in datasets.items():
        img = (
            ee.ImageCollection(collection_id)
            .select(band)
            .filterDate(start, end)
            .filterBounds(geometry)
            .mean()
            .rename(pollutant)
            .clip(geometry)
        )
        images[pollutant] = img

    # Stack all bands into one image
    stacked = images["NO2"]
    for p in ["SO2", "CO", "O3"]:
        stacked = stacked.addBands(images[p])

    points = ee.FeatureCollection([
        ee.Feature(ee.Geometry.Point([lon, lat]), {"city": city, "lat": lat, "lon": lon})
        for city, lat, lon in STATIONS
    ])

    sampled = stacked.sampleRegions(
        collection=points,
        scale=3500,
        geometries=True,
    )

    features = sampled.getInfo()["features"]
    rows = []
    for f in features:
        props = f["properties"]

        # Convert mol/m² to µg/m³ (approximate surface concentration)
        no2_mol = props.get("NO2", 0) or 0
        so2_mol = props.get("SO2", 0) or 0
        co_mol  = props.get("CO",  0) or 0
        o3_mol  = props.get("O3",  0) or 0

        rows.append({
            "city":       props.get("city"),
            "lat":        props.get("lat"),
            "lon":        props.get("lon"),
            "no2":        round(no2_mol * 46e6, 4),   # mol/m² → µg/m²
            "so2":        round(so2_mol * 64e6, 4),
            "co":         round(co_mol  * 28e6, 4),
            "o3":         round(o3_mol  * 48e6, 4),
            "start_date": start,
            "end_date":   end,
        })

    df = pd.DataFrame(rows)
    out_path = DATA_DIR / f"sentinel5p_{start}_{end}.csv"
    df.to_csv(out_path, index=False)
    logger.success(f"Saved Sentinel-5P data to {out_path}")
    return df


def fetch_hcho_grid(start: str, end: str, scale_km: int = 10) -> pd.DataFrame:
    """
    Fetch HCHO values on a regular grid over India.
    Used for hotspot detection and spatial mapping.
    Scale: 10km resolution.
    """
    init_gee()
    geometry = ee.Geometry.Rectangle(INDIA_BOX)

    hcho_img = (
        ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_HCHO")
        .select("tropospheric_HCHO_column_number_density")
        .filterDate(start, end)
        .filterBounds(geometry)
        .mean()
        .clip(geometry)
    )

    # Sample on a grid
    sampled = hcho_img.sample(
        region=geometry,
        scale=scale_km * 1000,
        projection='EPSG:4326',
        numPixels=5000,
        geometries=True,
    )

    features = sampled.getInfo()["features"]
    rows = []
    for f in features:
        coords = f["geometry"]["coordinates"]
        val    = f["properties"].get("tropospheric_HCHO_column_number_density", 0)
        if val and val > 0:
            rows.append({
                "lon":        coords[0],
                "lat":        coords[1],
                "hcho_value": val,
                "date":       start,
            })

    df = pd.DataFrame(rows)
    out_path = DATA_DIR / f"hcho_grid_{start}_{end}.csv"
    df.to_csv(out_path, index=False)
    logger.success(f"Fetched HCHO grid: {len(df)} points → {out_path}")
    return df