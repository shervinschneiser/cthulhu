from pydantic import BaseModel


class GatewayError(BaseModel):
    error: str
    status_code: int
    request_id: str | None = None
