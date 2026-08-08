from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cthulhu API Gateway"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str
    redis_url: str
    proxy_timeout: float = 30.0
    api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
