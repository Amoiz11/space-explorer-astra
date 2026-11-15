"""
Pydantic schemas for terrain-aware solar illumination (LL-14 to LL-16).
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class IlluminationPointModel(BaseModel):
    timestamp: str
    sun_azimuth: float
    sun_elevation: float
    sun_azimuth_deg: Optional[float] = None
    sun_elevation_deg: Optional[float] = None
    horizon_elevation_at_sun_azimuth: float
    sun_angular_radius_deg: float
    illuminated_fraction: float = Field(..., ge=0.0, le=1.0)
    status: str = Field(..., description="'lit', 'partial', or 'shadow'")


class IlluminationWindowModel(BaseModel):
    start: str
    end: str
    duration_hours: float


class IlluminationWindowsModel(BaseModel):
    any_part_lit: List[IlluminationWindowModel]
    fully_lit: List[IlluminationWindowModel]


class IlluminationTotalsModel(BaseModel):
    hours_any_part_lit: float
    hours_fully_lit: float
    hours_shadow: float
    total_simulation_hours: float
    number_of_windows: int
    shortest_window_hours: float
    longest_window_hours: float
    longest_continuous_shadow_hours: float
    boundary_refinement_method: str = "linear interpolation between time steps"


class SiteIlluminationResponse(BaseModel):
    site_id: str
    site_name: str
    is_placeholder: bool
    label: str = Field("Modelled", description="SRS status label")
    frame: str = "MOON_ME_DE421"
    product_id: str = "lola-dem-75s-240m"
    method: str = "SPICE geometric with terrain horizon from a 240 m DEM"
    observer_elevation_m: float
    observer_height_m: float
    total_observer_elevation_m: float
    kernels_used: List[str]
    series: List[IlluminationPointModel]
    windows: IlluminationWindowsModel
    totals: IlluminationTotalsModel
    disclaimers: List[str]
