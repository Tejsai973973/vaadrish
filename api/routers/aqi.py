from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from api.db.database import get_db
from api.db.models import AQIReading, Station
from api.schemas.aqi_schema import AQIGeoJSON, TimeSeriesResponse, NationalSummary
from geoalchemy2.functions import ST_X, ST_Y
from pipeline.openaq import run_openaq_pipeline
from datetime import date as date_type

router = APIRouter()


@router.get("/spatial", response_model=AQIGeoJSON,
            summary="AQI spatial data as GeoJSON for map rendering")
async def get_aqi_spatial(
    date: str = Query(default="2024-10-15", description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AQIReading, Station, ST_X(Station.location), ST_Y(Station.location))
        .join(Station, AQIReading.station_id == Station.id)
        .where(AQIReading.date == date)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No AQI data for date: {date}")

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "city":       station.city,
                "aqi":        int(reading.aqi_predicted or 0),
                "aqi_actual": int(reading.aqi_actual or 0),
                "pm25":       round(reading.pm25_predicted or 0, 1),
                "no2":        round(reading.no2 or 0, 1),
                "so2":        round(reading.so2 or 0, 1),
                "co":         round(reading.co or 0, 2),
                "o3":         round(reading.o3 or 0, 1),
                "category":   reading.category or "Unknown",
            },
        }
        for reading, station, lon, lat in rows
    ]
    return {"type": "FeatureCollection", "features": features}


@router.get("/timeseries", response_model=TimeSeriesResponse,
            summary="AQI time series — satellite vs CPCB ground truth")
async def get_timeseries(
    city:  str = Query(default="Delhi"),
    start: str = Query(default="2024-10-01"),
    end:   str = Query(default="2024-11-30"),
    db:    AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AQIReading, Station)
        .join(Station, AQIReading.station_id == Station.id)
        .where(
            and_(
                Station.city == city,
                AQIReading.date >= start,
                AQIReading.date <= end,
            )
        )
        .order_by(AQIReading.date)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for city: {city}")

    return {
        "city":         city,
        "dates":        [str(r.date) for r, _ in rows],
        "satellite":    [round(r.aqi_predicted or 0, 1) for r, _ in rows],
        "ground_truth": [round(r.aqi_actual or 0, 1) for r, _ in rows],
    }


@router.get("/national-summary", response_model=NationalSummary,
            summary="National AQI statistics for a given date")
async def get_national_summary(
    date: str = Query(default="2024-10-15"),
    db:   AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AQIReading, Station)
        .join(Station, AQIReading.station_id == Station.id)
        .where(AQIReading.date == date)
        .order_by(AQIReading.aqi_predicted.desc())
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for date: {date}")

    aqi_values = [r.aqi_predicted for r, _ in rows if r.aqi_predicted]
    top5 = [
        {"city": s.city, "aqi_predicted": r.aqi_predicted, "category": r.category}
        for r, s in rows[:5]
    ]
    category_counts = {}
    for r, _ in rows:
        category_counts[r.category] = category_counts.get(r.category, 0) + 1

    return {
        "national_avg":    int(sum(aqi_values) / len(aqi_values)),
        "max_aqi":         int(max(aqi_values)),
        "min_aqi":         int(min(aqi_values)),
        "top_5_polluted":  top5,
        "category_counts": category_counts,
    }

@router.post("/ingest",
             summary="Trigger OpenAQ ground station data ingestion")
async def ingest_aqi_data(
    target_date: str = Query(default="2024-10-15"),
    db: AsyncSession = Depends(get_db)
):
    result_date = date_type.fromisoformat(target_date)
    result = await run_openaq_pipeline(result_date, db)
    return {"status": "success", **result}