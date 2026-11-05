from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model_loaded: bool
    uptime_seconds: float

