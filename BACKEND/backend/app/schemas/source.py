from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel

class DataSourceInfo(BaseModel):
    id: str
    name: str
    source_url: Optional[str] = None
    organization: Optional[str] = None
    is_placeholder: bool = True

    class Config:
        from_attributes = True

class SourceProvenanceResponse(BaseModel):
    product_id: str
    product_identifier: str
    version: Optional[str] = None
    checksum: Optional[str] = None
    source: DataSourceInfo
    observation_time: Optional[datetime] = None
    retrieved_at: Optional[datetime] = None
    coordinate_frame: Optional[str] = None
    units: Optional[str] = None
    processing_method: Optional[str] = None
    uncertainty: Optional[Any] = None
    label: str = "Verified"  # Verified, Historical, Estimated, Unknown
    is_placeholder: bool = True

    class Config:
        from_attributes = True
