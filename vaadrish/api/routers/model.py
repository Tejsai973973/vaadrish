from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.db.database import get_db
from api.db.models import ModelMetric
from api.schemas.fire_schema import ModelMetricsResponse

router = APIRouter()


@router.get("/metrics", response_model=ModelMetricsResponse,
            summary="Latest CNN-LSTM model evaluation metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ModelMetric).order_by(ModelMetric.evaluated_at.desc()).limit(1)
    )
    metric = result.scalar_one_or_none()

    if not metric:
        # Return placeholder until model is trained
        return {
            "rmse":       0.0,
            "r2":         0.0,
            "mae":        0.0,
            "bias":       0.0,
            "pearson_r":  0.0,
            "n_stations": 0,
            "model_name": "CNN-LSTM-Attention (not trained yet)",
        }

    return {
        "rmse":       metric.rmse,
        "r2":         metric.r2,
        "mae":        metric.mae,
        "bias":       metric.bias,
        "pearson_r":  metric.pearson_r,
        "n_stations": metric.n_stations,
        "model_name": metric.model_name,
    }