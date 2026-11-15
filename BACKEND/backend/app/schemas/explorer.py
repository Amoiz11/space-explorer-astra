from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ExplorerResponse(BaseModel):
    id: str
    mission_id: str
    name: str
    explorer_type: str  # rover, lander, orbiter, probe
    current_status: str  # active, mission ended, inactive, unknown
    label: str = "Verified"  # Verified, Historical, Estimated, Unknown
    source_label: str = "NASA PDS / Mission Catalog"
    is_placeholder: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ExplorerDetailResponse(ExplorerResponse):
    pass
