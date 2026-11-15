from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel

class CoordinateValues(BaseModel):
    values: list
    units: str
    coordinate_frame: str

class LocationResponse(BaseModel):
    explorer_id: str
    position_status: str  # verified, historical, estimated, unknown
    label: str = "Verified"  # Verified, Historical, Estimated, Unknown
    observed_at: Optional[datetime] = None
    sol: Optional[int] = None
    sclk: Optional[str] = None
    coordinates: Optional[CoordinateValues] = None
    original_fields: Optional[Dict[str, Any]] = None
    uncertainty: Optional[Any] = None
    position_method: str = "localized"  # localized, derived, interpolated, unknown
    source_product_id: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    source_label: str = "NASA PDS PLACES"
    is_placeholder: bool = True

    class Config:
        from_attributes = True
