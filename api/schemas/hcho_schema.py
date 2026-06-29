from pydantic import BaseModel
from typing import Optional
from datetime import date


class HCHOFeatureProperties(BaseModel):
    hcho:       float
    z_score:    Optional[float] = None
    is_hotspot: bool = False


class HCHOFeature(BaseModel):
    type:       str = "Feature"
    geometry:   dict
    properties: HCHOFeatureProperties


class HCHOGeoJSON(BaseModel):
    type:     str = "FeatureCollection"
    features: list[HCHOFeature]


class HotspotResponse(BaseModel):
    cluster_id:    int
    center_lat:    float
    center_lon:    float
    mean_hcho:     float
    max_hcho:      float
    intensity:     str
    source_region: str
    point_count:   int


class HotspotsListResponse(BaseModel):
    hotspots:       list[HotspotResponse]
    total_hotspots: int