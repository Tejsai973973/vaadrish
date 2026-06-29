from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class AQIProperties(BaseModel):
    city:          str
    aqi:           int   = Field(..., ge=0, le=500)
    aqi_actual:    Optional[int] = None
    pm25:          float
    no2:           float
    so2:           float
    co:            float
    o3:            float
    category:      str


class AQIFeature(BaseModel):
    type:       str = "Feature"
    geometry:   dict
    properties: AQIProperties


class AQIGeoJSON(BaseModel):
    type:     str = "FeatureCollection"
    features: list[AQIFeature]


class TimeSeriesResponse(BaseModel):
    city:         str
    dates:        list[str]
    satellite:    list[float]
    ground_truth: list[float]


class NationalSummary(BaseModel):
    national_avg:    int
    max_aqi:         int
    min_aqi:         int
    top_5_polluted:  list[dict]
    category_counts: dict[str, int]