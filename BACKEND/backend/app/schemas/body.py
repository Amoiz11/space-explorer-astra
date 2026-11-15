from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class CelestialBodyResponse(BaseModel):
    id: str
    name: str
    body_type: str
    reference_system: str
    is_placeholder: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
