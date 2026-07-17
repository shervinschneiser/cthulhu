from fastapi import APIRouter
from redis import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine

router = APIRouter(prefix="/health", tags=["Health"])

settings = get_settings()


@router.get("")
async def health_check() -> dict:
    database = "down"
    redis = "down"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database = "up"
    except Exception:
        pass

    try:
        client = Redis.from_url(settings.redis_url)
        client.ping()
        redis = "up"
    except Exception:
        pass

    return {
        "status": "healthy" if database == "up" and redis == "up" else "degraded",
        "services": {
            "application": "up",
            "database": database,
            "redis": redis,
        },
    }
