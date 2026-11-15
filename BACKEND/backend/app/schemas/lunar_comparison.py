"""
Schemas for POST /api/v1/lunar/compare (B5a: LL-27 to LL-30).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class WindowRequest(BaseModel):
    start: str = Field(..., description="UTC start (ISO 8601 or YYYY-MM-DD)")
    days: int = Field(..., ge=1, le=60, description="Duration in days (1–60)")


class CriterionModel(BaseModel):
    """
    One user-supplied threshold.
    Label: 'example threshold, not an official safety criterion'.
    """
    metric: str = Field(
        ...,
        description=(
            "Metric to threshold: 'max_mean_slope_deg', 'min_any_lit_hours', "
            "'min_earth_visible_hours', 'min_both_up_hours', 'max_longest_shadow_hours'"
        ),
    )
    threshold: float = Field(..., description="Numeric threshold value")
    label: str = Field(
        "example threshold, not an official safety criterion",
        description="Human-readable label; always marked as example, not an official criterion",
    )


class PanelInputs(BaseModel):
    panel_area_m2: float = Field(..., gt=0)
    efficiency: float = Field(..., gt=0, le=1)
    tilt_deg: float = Field(..., ge=0, le=90)
    panel_azimuth_deg: float = Field(..., ge=0, le=360)
    track_sun_azimuth: bool = False


class CompareRequest(BaseModel):
    site_ids: List[str] = Field(..., min_length=1, max_length=5)
    windows: List[WindowRequest] = Field(..., min_length=1, max_length=4)
    step_minutes: int = Field(30, ge=15, description="Time step in minutes (minimum 15)")
    observer_height_m: float = Field(0.0, ge=0)
    criteria: Optional[List[CriterionModel]] = None
    panel: Optional[PanelInputs] = None

    @field_validator("site_ids")
    @classmethod
    def no_duplicate_sites(cls, v: List[str]) -> List[str]:
        seen = set()
        for s in v:
            if s in seen:
                raise ValueError(f"Duplicate site_id: '{s}'")
            seen.add(s)
        return v

    @field_validator("windows")
    @classmethod
    def no_duplicate_windows(cls, v: List[WindowRequest]) -> List[WindowRequest]:
        seen = set()
        for w in v:
            key = (w.start, w.days)
            if key in seen:
                raise ValueError(f"Duplicate window: start={w.start}, days={w.days}")
            seen.add(key)
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class IlluminationMetrics(BaseModel):
    hours_any_part_lit: float
    hours_fully_lit: float
    hours_shadow: float
    longest_shadow_hours: float
    number_of_lit_windows: int


class EarthMetrics(BaseModel):
    hours_earth_visible: float
    hours_earth_blocked: float
    number_of_earth_windows: int


class SlopeMetrics(BaseModel):
    mean_slope_deg: float
    max_slope_deg: float
    p90_slope_deg: float


class ElevationMetrics(BaseModel):
    mean_elevation_m: float
    relief_m: float


class CriterionResult(BaseModel):
    metric: str
    threshold: float
    label: str
    value: float
    passed: bool


class DataQuality(BaseModel):
    dem_resolution_m: int
    is_placeholder: bool
    kernels_used: List[str]
    horizon_type: str
    notes: List[str]


class ComparisonRow(BaseModel):
    site_id: str
    site_name: str
    is_placeholder: bool
    window_start: str
    window_days: int
    observer_elevation_m: float

    illumination: IlluminationMetrics
    earth: EarthMetrics
    slope: SlopeMetrics
    elevation: ElevationMetrics
    hours_both_up: float

    energy_kwh: Optional[float] = None

    criteria_results: List[CriterionResult] = []
    data_quality: DataQuality


class BestBy(BaseModel):
    best_for_sunlight: Optional[str] = None      # site_id:window_start with most any-part-lit hours
    best_for_earth_visibility: Optional[str] = None
    lowest_slope: Optional[str] = None           # row with lowest mean slope
    most_hours_both_up: Optional[str] = None


class CompareResponse(BaseModel):
    id: int
    label: str
    method: str
    kernels_used: List[str]
    settings: Dict[str, Any]
    rows: List[ComparisonRow]
    best_by: BestBy
    criteria: List[CriterionModel]
    disclaimers: List[str]


class ExportRow(BaseModel):
    site_id: str
    site_name: str
    window_start: str
    window_days: int
    hours_any_part_lit: float
    hours_fully_lit: float
    hours_shadow: float
    longest_shadow_hours: float
    number_of_lit_windows: int
    hours_earth_visible: float
    hours_earth_blocked: float
    number_of_earth_windows: int
    hours_both_up: float
    mean_slope_deg: float
    max_slope_deg: float
    p90_slope_deg: float
    mean_elevation_m: float
    relief_m: float
    energy_kwh: Optional[float] = None
    criteria_results: List[Dict[str, Any]] = []
