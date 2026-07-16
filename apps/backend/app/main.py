from fastapi import FastAPI
from app.core.logging import configure_logging
from app.middleware import RequestIDMiddleware

configure_logging()

app = FastAPI(
    title="Cthulhu API Gateway",
    version="0.1.0",
)

app.add_middleware(RequestIDMiddleware)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Cthulhu API Gateway"}
