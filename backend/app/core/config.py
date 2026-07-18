from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), extra="ignore", case_sensitive=False
    )

    app_name: str = "Stock Agent Ops"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./stock_agent_ops.db"
    redis_url: str = "redis://localhost:6379/0"
    alpha_vantage_api_key: str = Field(default="")
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"
    frontend_origin: str = "http://localhost:5173"
    cache_ttl_seconds: int = 300
    redis_timeout_seconds: float = 0.25
    alpha_vantage_timeout_seconds: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
