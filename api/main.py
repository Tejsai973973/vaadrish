from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.core.config import get_settings
from api.core.logger import setup_logger
from api.db.database import create_tables
from api.routers import aqi, hcho, fire, model, ws

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
   #startup
    setup_logger(debug=settings.debug)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await create_tables()
    logger.info("Database tables ready ✅")
    yield
    #Shutdown 
    logger.info("Shutting down Vaadrish...")


app = FastAPI(
    title=settings.app_name,
    description="ISRO PS-03: Surface AQI & HCHO Hotspot Detection API",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Routers
app.include_router(aqi.router,   prefix="/api/aqi",   tags=["AQI"])
app.include_router(hcho.router,  prefix="/api/hcho",  tags=["HCHO"])
app.include_router(fire.router,  prefix="/api/fire",  tags=["Fire"])
app.include_router(model.router, prefix="/api/model", tags=["Model"])
app.include_router(ws.router,    tags=["WebSocket"])


@app.get("/api/health", tags=["Health"])
async def health():
    return {
        "status":  "online",
        "version": settings.app_version,
        "app":     settings.app_name,
    }