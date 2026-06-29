from pydantic import BaseModel
from datetime import date


class FirePoint(BaseModel):
    lat:        float
    lon:        float
    date:       str
    frp:        float
    confidence: str
    source:     str


class CorrelationResponse(BaseModel):
    pearson_r:    float
    p_value:      float
    scatter_data: list[dict]
    best_lag_days: int


class ModelMetricsResponse(BaseModel):
    rmse:       float
    r2:         float
    mae:        float
    bias:       float
    pearson_r:  float
    n_stations: int
    model_name: str