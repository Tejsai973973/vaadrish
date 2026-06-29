from sqlalchemy import (
    Column, Integer, Float, String,
    DateTime, Boolean, Date, ForeignKey, func
)
from geoalchemy2 import Geometry
from api.db.database import Base


class Station(Base):
    """CPCB / OpenAQ ground monitoring stations."""
    __tablename__ = "stations"

    id         = Column(Integer, primary_key=True, index=True)
    city       = Column(String, nullable=False, index=True)
    state      = Column(String)
    source     = Column(String, default="CPCB")   
    location   = Column(Geometry("POINT", srid=4326))
    elevation  = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class AQIReading(Base):
    """Satellite-predicted + CPCB ground AQI per station per day."""
    __tablename__ = "aqi_readings"

    id             = Column(Integer, primary_key=True, index=True)
    station_id     = Column(Integer, ForeignKey("stations.id"), index=True)
    date           = Column(Date, nullable=False, index=True)
    aqi_predicted  = Column(Float)
    aqi_actual     = Column(Float, nullable=True)
    pm25_predicted = Column(Float)
    pm25_actual    = Column(Float, nullable=True)
    no2            = Column(Float)
    so2            = Column(Float)
    co             = Column(Float)
    o3             = Column(Float)
    hcho           = Column(Float, nullable=True)
    category       = Column(String)


class HCHOReading(Base):
    """Sentinel-5P TROPOMI HCHO column per grid point per day."""
    __tablename__ = "hcho_readings"

    id          = Column(Integer, primary_key=True, index=True)
    date        = Column(Date, nullable=False, index=True)
    location    = Column(Geometry("POINT", srid=4326))
    hcho_value  = Column(Float)    # mol/m²
    z_score     = Column(Float, nullable=True)
    is_hotspot  = Column(Boolean, default=False)
    qa_value    = Column(Float, default=1.0)


class FireEvent(Base):
    """MODIS / VIIRS active fire events."""
    __tablename__ = "fire_events"

    id         = Column(Integer, primary_key=True, index=True)
    date       = Column(Date, nullable=False, index=True)
    location   = Column(Geometry("POINT", srid=4326))
    frp        = Column(Float)     
    confidence = Column(String)    
    source     = Column(String)    


class HCHOHotspot(Base):
    """Detected HCHO hotspot clusters from DBSCAN."""
    __tablename__ = "hcho_hotspots"

    id            = Column(Integer, primary_key=True, index=True)
    date          = Column(Date, nullable=False, index=True)
    cluster_id    = Column(Integer)
    center        = Column(Geometry("POINT", srid=4326))
    mean_hcho     = Column(Float)
    max_hcho      = Column(Float)
    intensity     = Column(String)   
    source_region = Column(String)
    point_count   = Column(Integer)


class ModelMetric(Base):
    """Stored evaluation metrics for the CNN-LSTM model."""
    __tablename__ = "model_metrics"

    id           = Column(Integer, primary_key=True, index=True)
    model_name   = Column(String, default="CNN-LSTM-Attention")
    evaluated_at = Column(DateTime, server_default=func.now())
    rmse         = Column(Float)
    r2           = Column(Float)
    mae          = Column(Float)
    bias         = Column(Float)
    pearson_r    = Column(Float)
    n_stations   = Column(Integer)