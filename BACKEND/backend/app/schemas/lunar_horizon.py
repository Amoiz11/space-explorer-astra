"""
Schemas for lunar horizon profile (Phase B3b: LL-11 to LL-13, LL-17).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class HorizonPointModel(BaseModel):
    azimuth_deg: float
    horizon_elevation_deg: float
    distance_to_blocking_pixel_km: float
    cut_by_coverage: bool


class HorizonSummaryModel(BaseModel):
    min_horizon_elevation_deg: float
    max_horizon_elevation_deg: float
    mean_horizon_elevation_deg: float
    max_horizon_azimuth_deg: float
    cut_azimuth_count: int


class HorizonProfileResponse(BaseModel):
    site_id: str
    site_name: str
    is_placeholder: bool
    label: str = Field("Derived", description="Label per SRS (Derived for DEM computed profiles)")
    product_id: str
    resolution: str
    method: str
    observer_height_dem_m: float
    observer_height_m: float
    total_observer_height_m: float
    summary: HorizonSummaryModel
    cut_azimuths: List[float]
    profile: List[HorizonPointModel]
    disclaimers: List[str]
