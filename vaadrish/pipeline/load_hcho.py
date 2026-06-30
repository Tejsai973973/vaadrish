import asyncio
from datetime import date as date_type
import pandas as pd
from pathlib import Path
from loguru import logger
from geoalchemy2.elements import WKTElement

from api.db.database import AsyncSessionFactory as SessionLocal
from api.db.models import HCHOReading, HCHOHotspot
from ml.hcho_hotspot.detector import HCHOHotspotDetector

async def load_hcho_grid(csv_path: str):
    df = pd.read_csv(csv_path)
    if df.empty:
        logger.error(f"Empty data in {csv_path}")
        return

    logger.info(f"Loaded {len(df)} grid points. Detecting hotspots...")
    
    detector = HCHOHotspotDetector(z_threshold=1.5, dbscan_eps=1.0, dbscan_min_samples=3)
    anomaly_df = detector.detect_anomalies(df)
    anomalies, hotspots = detector.cluster_hotspots(anomaly_df)
    
    # Merge cluster info back
    if not anomalies.empty:
        anomaly_df = anomaly_df.merge(
            anomalies[['lat', 'lon', 'cluster_id', 'is_hotspot']], 
            on=['lat', 'lon'], how='left'
        )
        anomaly_df['is_hotspot'] = anomaly_df['is_hotspot'].fillna(False)
    else:
        anomaly_df['is_hotspot'] = False

    async with SessionLocal() as db:
        logger.info("Inserting HCHO grid into database...")
        # Clear existing data for these dates (simplified)
        await db.execute(HCHOReading.__table__.delete())
        await db.execute(HCHOHotspot.__table__.delete())
        
        # Insert readings
        readings = []
        for _, row in anomaly_df.iterrows():
            pt = WKTElement(f"POINT({row['lon']} {row['lat']})", srid=4326)
            readings.append(
                HCHOReading(
                    location=pt,
                    hcho_value=row['hcho_value'],
                    date=pd.to_datetime(row['date']).date(),
                    z_score=row['z_score'],
                    is_hotspot=row['is_hotspot']
                )
            )
        
        db.add_all(readings)
        
        # Insert hotspots
        if not hotspots.empty:
            logger.info(f"Inserting {len(hotspots)} hotspots...")
            db_hotspots = []
            for _, row in hotspots.iterrows():
                pt = WKTElement(f"POINT({row['center_lon']} {row['center_lat']})", srid=4326)
                db_hotspots.append(
                    HCHOHotspot(
                        center=pt,
                        mean_hcho=row['mean_hcho'],
                        max_hcho=row['max_hcho'],
                        date=pd.to_datetime(df['date'].iloc[0]).date(),
                        intensity=row['intensity'],
                        point_count=row['point_count'],
                        source_region="Unknown"
                    )
                )
            db.add_all(db_hotspots)

        await db.commit()
        logger.success("HCHO data and hotspots loaded successfully.")

if __name__ == "__main__":
    grid_csv = Path("data/raw/gee").glob("hcho_grid_*.csv")
    csv_file = list(grid_csv)[0]
    asyncio.run(load_hcho_grid(csv_file))
