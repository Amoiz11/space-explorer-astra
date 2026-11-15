from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class MissionResponse(BaseModel):
    id: str
    body_id: str
    name: str
    launch_date: Optional[datetime] = None
    landing_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str
    label: str = "Historical"  # Verified, Historical, Estimated, Unknown
    source_label: str = "NASA Mission Archive"
    is_placeholder: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
