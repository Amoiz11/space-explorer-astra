"""
Pydantic schemas for direct-to-Earth line-of-sight visibility (LL-19 to LL-22).
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class EarthVisibilityPointModel(BaseModel):
    timestamp: str
    earth_azimuth: float
    earth_elevation: float
    earth_azimuth_deg: Optional[float] = None
    earth_elevation_deg: Optional[float] = None
    horizon_elevation_at_earth_azimuth: float
    effective_elevation_deg: float
    earth_angular_radius_deg: float
    obstruction_status: str = Field(..., description="'clear', 'blocked_by_terrain', or 'below_horizon'")
    earth_visible: bool


class EarthVisibilityWindowModel(BaseModel):
    start: str
    end: str
    duration_hours: float
    mean_earth_azimuth: float
    mean_earth_elevation: float


class EarthVisibilityTotalsModel(BaseModel):
    earth_visible_hours: float
    blocked_by_terrain_hours: float
    below_horizon_hours: float
    total_simulation_hours: float
    earth_visible_fraction: float
    number_of_windows: int
    boundary_refinement_method: str = "linear interpolation between time steps"


class SiteEarthVisibilityResponse(BaseModel):
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
    earth_disk_criterion: str = Field("center", description="'center' or 'upper_limb'")
    series: List[EarthVisibilityPointModel]
    windows: List[EarthVisibilityWindowModel]
    totals: EarthVisibilityTotalsModel
    relay_communication: str = "not modelled"
    relay_communication_note: str
    disclaimers: List[str]
