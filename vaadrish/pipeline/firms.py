import pandas as pd
from datetime import date
from pathlib import Path
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import date as date_type


RAW_DATA_DIR = Path("data/raw")
FIRE_CSV = RAW_DATA_DIR / "fire_india_2024.csv"


def load_fire_csv() -> pd.DataFrame:
    """Load downloaded FIRMS CSV file."""
    if not FIRE_CSV.exists():
        raise FileNotFoundError(
            f"Fire data CSV not found at {FIRE_CSV}. "
            "Download from: https://firms.modaps.eosdis.nasa.gov/download/"
        )
    df = pd.read_csv(FIRE_CSV)
    logger.info(f"Loaded {len(df)} fire records from {FIRE_CSV}")
    return df


def parse_confidence(raw) -> str:
    """Convert VIIRS confidence to low/nominal/high."""
    if isinstance(raw, (int, float)):
        val = int(raw)
        if val >= 80:   return "high"
        if val >= 50:   return "nominal"
        return "low"
    mapping = {"l": "low", "n": "nominal", "h": "high"}
    return mapping.get(str(raw).lower(), "nominal")


async def save_fire_data(df: pd.DataFrame, db: AsyncSession) -> int:
    if df.empty:
        return 0

    import json
    from datetime import date as date_type

    source = "VIIRS" if "bright_ti4" in df.columns else "MODIS"
    rows = []

    for _, row in df.iterrows():
        try:
            rows.append({
                "date":       str(date_type.fromisoformat(str(row["acq_date"])[:10])),
                "geom":       f"POINT({float(row['longitude'])} {float(row['latitude'])})",
                "frp":        float(row.get("frp", 0) or 0),
                "confidence": parse_confidence(row.get("confidence", "n")),
                "source":     source,
            })
        except Exception as e:
            logger.error(f"Row parse error: {e}")
            continue

    if rows:
        await db.execute(
            text("""
                INSERT INTO fire_events (date, location, frp, confidence, source)
                SELECT
                    CAST(r.date AS date),
                    ST_GeomFromText(r.geom, 4326),
                    r.frp,
                    r.confidence,
                    r.source
                FROM jsonb_to_recordset(CAST(:data AS jsonb)) AS r(
                    date text, geom text, frp float, confidence text, source text
                )
                ON CONFLICT DO NOTHING
            """),
            {"data": json.dumps(rows)},
        )
        await db.commit()

    logger.success(f"Inserted {len(rows)} fire events ✅")
    return len(rows)


async def run_firms_pipeline(
    start: date,
    end:   date,
    db:    AsyncSession
) -> int:
    """Full pipeline: load CSV → filter by date → save to DB."""
    df = load_fire_csv()

    # Filter by date range
    df["acq_date"] = pd.to_datetime(df["acq_date"]).dt.date
    df = df[(df["acq_date"] >= start) & (df["acq_date"] <= end)]
    logger.info(f"Filtered to {len(df)} records between {start} and {end}")

    return await save_fire_data(df, db)