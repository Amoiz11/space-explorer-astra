"""
Schemas for lunar topocentric geometry and site comparison (LL-11 to LL-13, LL-17, LL-18).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GeometryPointModel(BaseModel):
    timestamp: str
    sun_azimuth_deg: float
    sun_elevation_deg: float
    earth_azimuth_deg: float
    earth_elevation_deg: float
    sun_visible: bool
    earth_visible: bool
    joint_visible: bool
    horizon_elevation_at_sun_azimuth: Optional[float] = None
    horizon_elevation_at_earth_azimuth: Optional[float] = None


class WindowModel(BaseModel):
    start: str
    end: str
    duration_hours: float
    steps: int


class WindowsModel(BaseModel):
    sunlight: List[WindowModel]
    earth_visibility: List[WindowModel]
    joint_visibility: List[WindowModel]


class TotalsModel(BaseModel):
    sunlight_hours: float
    earth_visible_hours: float
    joint_sunlight_and_earth_visible_hours: float
    total_simulation_hours: float
    sunlight_fraction: float
    earth_visible_fraction: float


class SiteGeometryResponse(BaseModel):
    site_id: str
    site_name: str
    is_placeholder: bool
    label: str = Field("Modelled", description="Label per SRS (Modelled for simulated geometric predictions)")
    frame: str
    method: str
    observer_elevation_m: float
    reference_sphere_radius_km: float
    kernels_used: List[str]
    series: List[GeometryPointModel]
    windows: WindowsModel
    totals: TotalsModel
    disclaimers: List[str]


class SiteComparisonItemModel(BaseModel):
    site_id: str
    site_name: str
    is_placeholder: bool
    coordinates: List[float]
    elevation_m: float
    totals: TotalsModel


class SiteComparisonResponse(BaseModel):
    label: str = Field("Modelled", description="Label per SRS")
    frame: str
    method: str
    start_utc: str
    days: int
    step_minutes: int
    kernels_used: List[str]
    sites: List[SiteComparisonItemModel]
    disclaimers: List[str]
