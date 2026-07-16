from fastapi import FastAPI
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="Cthulhu API Gateway",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Cthulhu API Gateway"}
