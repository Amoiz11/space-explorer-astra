"""
Schemas for lunar site terrain and slope analysis (LL-06 to LL-10).
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ElevationStatsModel(BaseModel):
    min_m: float
    max_m: float
    mean_m: float
    local_relief_m: float
    roughness_rms_m: float
    roughness_method: str
    vertical_reference: str


class HistogramModel(BaseModel):
    counts: List[int]
    bin_edges_deg: List[float]
    total_pixels: int


class SlopeStatsModel(BaseModel):
    mean_deg: float
    max_deg: float
    min_deg: float
    p50_deg: float
    p90_deg: float
    p95_deg: float
    method: str
    pixel_spacing_m: float
    histogram: HistogramModel


class CriteriaResultModel(BaseModel):
    slope_threshold_deg: float
    threshold_label: str
    exceeding_pixel_count: int
    total_pixel_count: int
    fraction_exceeding_threshold: float
    percentage_exceeding_threshold: float
    site_safety_disclaimer: str


class TerrainAnalysisResponse(BaseModel):
    site_id: str
    site_name: str
    is_placeholder: bool
    label: str = Field("Derived", description="Label per SRS (Derived for DEM products)")
    product_id: str
    resolution: str
    coverage: Dict[str, Any]
    vertical_reference: str
    no_data_value: Optional[str]
    coordinate_reference_note: str
    method: str
    units: str
    pixel_count: int
    elevation: ElevationStatsModel
    criteria_result: CriteriaResultModel
    scale_distortion_note: str
    disclaimer: str


class SlopeAnalysisResponse(BaseModel):
    site_id: str
    site_name: str
    is_placeholder: bool
    label: str = Field("Derived", description="Label per SRS (Derived for DEM products)")
    product_id: str
    resolution: str
    coverage: Dict[str, Any]
    vertical_reference: str
    no_data_value: Optional[str]
    coordinate_reference_note: str
    method: str
    units: str
    pixel_count: int
    slope: SlopeStatsModel
    criteria_result: CriteriaResultModel
    scale_distortion_note: str
    disclaimer: str
