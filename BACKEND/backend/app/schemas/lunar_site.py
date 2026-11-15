from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CoordinateModel(BaseModel):
    values: List[float] = Field(..., description="Original coordinate values (e.g. [latitude, longitude])")
    units: str = Field(..., description="Coordinate units, e.g. deg")
    frame: str = Field(..., description="Documented coordinate reference frame, e.g. MOON_ME_DE421")

class CandidateLandingSiteBase(BaseModel):
    name: str
    body_id: str = Field(..., description="Celestial body ID (e.g. moon)")
    coordinates: CoordinateModel
    frame: str
    analysis_radius_m: float = 1000.0
    semi_major_m: Optional[float] = None
    semi_minor_m: Optional[float] = None
    orientation_deg: Optional[float] = None
    criteria: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_placeholder: bool = True

class CandidateLandingSiteCreate(CandidateLandingSiteBase):
    id: str

class CandidateLandingSiteUpdate(BaseModel):
    name: Optional[str] = None
    coordinates: Optional[CoordinateModel] = None
    frame: Optional[str] = None
    analysis_radius_m: Optional[float] = None
    semi_major_m: Optional[float] = None
    semi_minor_m: Optional[float] = None
    orientation_deg: Optional[float] = None
    criteria: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_placeholder: Optional[bool] = None

class CandidateLandingSiteResponse(CandidateLandingSiteBase):
    id: str

    class Config:
        from_attributes = True
