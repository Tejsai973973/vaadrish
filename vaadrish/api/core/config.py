from pydantic_settings import BaseSettings
from pydantic import AnyUrl
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Vaadrish"
    app_version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str

    gee_project: str = "gen-lang-client-0538429077"
    nasa_firms_api_key: str = ""
    openaq_api_key: str = ""
    cds_api_key: str = ""

    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()