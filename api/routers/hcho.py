from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from api.db.database import get_db
from api.db.models import HCHOReading, HCHOHotspot
from api.schemas.hcho_schema import HCHOGeoJSON, HotspotsListResponse
from geoalchemy2.functions import ST_X, ST_Y

router = APIRouter()


@router.get("/spatial", response_model=HCHOGeoJSON,
            summary="HCHO spatial data as GeoJSON")
async def get_hcho_spatial(
    date: str = Query(default="2024-10-15"),
    db:   AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(HCHOReading, ST_X(HCHOReading.location), ST_Y(HCHOReading.location))
        .where(HCHOReading.date == date)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No HCHO data for date: {date}")

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "hcho":       float(r.hcho_value or 0),
                "z_score":    round(float(r.z_score or 0), 2),
                "is_hotspot": bool(r.is_hotspot),
            },
        }
        for r, lon, lat in rows
    ]
    return {"type": "FeatureCollection", "features": features}


@router.get("/hotspots", response_model=HotspotsListResponse,
            summary="HCHO hotspot clusters detected by DBSCAN")
async def get_hotspots(
    date:   str = Query(default="2024-10-15"),
    db:     AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(HCHOHotspot, ST_X(HCHOHotspot.center), ST_Y(HCHOHotspot.center))
        .where(HCHOHotspot.date <= date)
        .order_by(HCHOHotspot.mean_hcho.desc())
    )
    rows = result.all()

    hotspots = [
        {
            "cluster_id":    h.cluster_id,
            "center_lat":    lat,
            "center_lon":    lon,
            "mean_hcho":     h.mean_hcho,
            "max_hcho":      h.max_hcho,
            "intensity":     h.intensity,
            "source_region": h.source_region,
            "point_count":   h.point_count,
        }
        for h, lon, lat in rows
    ]
    return {"hotspots": hotspots, "total_hotspots": len(hotspots)}