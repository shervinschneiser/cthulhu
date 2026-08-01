from redis import Redis

from app.core.config import settings


def check_redis() -> bool:
    client = Redis.from_url(settings.redis_url)

    try:
        return client.ping()
    finally:
        client.close()
