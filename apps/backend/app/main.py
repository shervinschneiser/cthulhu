from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.gateway import proxy
from app.api.gateway import router as gateway_router
from app.api.health import router as health_router
from app.core.constants import APP_NAME, APP_VERSION
from app.core.logging import configure_logging
from app.middleware import RequestIDMiddleware

from app.middleware.request_logging import RequestLoggingMiddleware

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await proxy.close()


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router)
app.include_router(gateway_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Cthulhu API Gateway"}
