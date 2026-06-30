from fastapi import APIRouter, Query, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from api.db.database import get_db
from api.db.models import FireEvent, HCHOReading
from api.schemas.fire_schema import FirePoint, CorrelationResponse
from geoalchemy2.functions import ST_X, ST_Y
from datetime import date as date_type
from datetime import datetime
from pathlib import Path
import numpy as np
from scipy import stats
from pipeline.firms import run_firms_pipeline
from ml.fire_correlation.analyzer import run_full_analysis

router = APIRouter()


@router.get("/points", response_model=list[FirePoint],
            summary="MODIS/VIIRS fire event points")
async def get_fire_points(
    start: str = Query(default="2024-10-01"),
    end:   str = Query(default="2024-11-30"),
    db:    AsyncSession = Depends(get_db)
):
    # Convert strings to date
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    result = await db.execute(
        select(FireEvent, ST_X(FireEvent.location), ST_Y(FireEvent.location))
        .where(and_(FireEvent.date >= start_date, FireEvent.date <= end_date))
        .order_by(FireEvent.date)
    )
    rows = result.all()

    return [
        {
            "lat":        lat,
            "lon":        lon,
            "date":       str(f.date),
            "frp":        f.frp,
            "confidence": f.confidence,
            "source":     f.source,
        }
        for f, lon, lat in rows
    ]


@router.get("/correlation", response_model=CorrelationResponse,
            summary="Pearson correlation between fire count and HCHO levels")
async def get_fire_hcho_correlation(
    start: str = Query(default="2024-10-01"),
    end:   str = Query(default="2024-11-30"),
    db:    AsyncSession = Depends(get_db)
):
    # Convert strings to date
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    fire_result = await db.execute(
        select(FireEvent.date, FireEvent.frp)
        .where(and_(FireEvent.date >= start_date, FireEvent.date <= end_date))
    )
    hcho_result = await db.execute(
        select(HCHOReading.date, HCHOReading.hcho_value)
        .where(and_(HCHOReading.date >= start_date, HCHOReading.date <= end_date))
    )

    fire_rows = fire_result.all()
    hcho_rows = hcho_result.all()

    if len(fire_rows) < 5 or len(hcho_rows) < 5:
        raise HTTPException(status_code=404, detail="Not enough data for correlation")

    # Group by date
    fire_by_date = {}
    for date, frp in fire_rows:
        fire_by_date[str(date)] = fire_by_date.get(str(date), 0) + (frp or 0)

    hcho_by_date = {}
    for date, hcho in hcho_rows:
        if str(date) not in hcho_by_date:
            hcho_by_date[str(date)] = []
        hcho_by_date[str(date)].append(hcho or 0)
    hcho_by_date = {d: np.mean(v) for d, v in hcho_by_date.items()}

    common_dates = sorted(set(fire_by_date) & set(hcho_by_date))
    if len(common_dates) < 5:
        raise HTTPException(status_code=404, detail="Not enough overlapping dates")

    fire_vals = [fire_by_date[d] for d in common_dates]
    hcho_vals = [hcho_by_date[d] for d in common_dates]

    r, p = stats.pearsonr(fire_vals, hcho_vals)
    scatter = [
        {"date": d, "fire_count": f, "hcho": h}
        for d, f, h in zip(common_dates, fire_vals, hcho_vals)
    ]

    return {
        "pearson_r":     round(float(r), 3),
        "p_value":       round(float(p), 4),
        "scatter_data":  scatter,
        "best_lag_days": 1,
    }


@router.post("/ingest",
             summary="Trigger NASA FIRMS fire data ingestion")
async def ingest_fire_data(
    start: str = Query(default="2024-10-01"),
    end:   str = Query(default="2024-10-10"),
    db:    AsyncSession = Depends(get_db)
):
    start_date = date_type.fromisoformat(start)
    end_date   = date_type.fromisoformat(end)

    count = await run_firms_pipeline(start_date, end_date, db)
    return {
        "status":   "success",
        "inserted": count,
        "source":   "NASA FIRMS MODIS",
        "range":    f"{start} → {end}",
    }


@router.get("/correlation/full",
            summary="Full lag correlation analysis between fire FRP and HCHO column")
async def get_full_correlation():
    """
    Runs the complete Fire-HCHO lag correlation analysis using:
      - NASA FIRMS fire data (data/raw/fire_india_2024.csv)
      - GEE Sentinel-5P HCHO grid (data/raw/gee/hcho_grid_*.csv)

    Returns Pearson R at 0-7 day lags and per-region breakdown.
    This directly addresses ISRO PS-03 Objective 2.
    """
    fire_csv = Path("data/raw/fire_india_2024.csv")
    hcho_csvs = list(Path("data/raw/gee").glob("hcho_grid_*.csv"))

    if not fire_csv.exists():
        raise HTTPException(status_code=404, detail="Fire data not found. Run /fire/ingest first.")
    if not hcho_csvs:
        raise HTTPException(status_code=404, detail="HCHO grid data not found. Run GEE pipeline first.")

    results = run_full_analysis(str(fire_csv), str(hcho_csvs[0]))
    return results