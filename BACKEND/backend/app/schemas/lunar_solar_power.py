"""
Pydantic schemas for solar irradiance and power opportunity estimation (LL-23 to LL-26).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PanelInputsModel(BaseModel):
    panel_area_m2: float = Field(..., gt=0.0, description="Solar panel active area in square metres (> 0)")
    efficiency: float = Field(..., ge=0.0, le=1.0, description="Panel conversion efficiency (0 to 1)")
    tilt_deg: float = Field(0.0, ge=0.0, le=180.0, description="Panel tilt from horizontal: 0 = horizontal, 90 = vertical")
    panel_azimuth_deg: float = Field(0.0, ge=0.0, le=360.0, description="Panel pointing azimuth in degrees clockwise from North toward East")
    track_sun_azimuth: bool = Field(False, description="When true, panel continuously tracks Sun's azimuth keeping fixed tilt")


class SolarEstimateRequest(BaseModel):
    start: str = Field(..., description="UTC start date/time (e.g. YYYY-MM-DD or ISO 8601)")
    days: int = Field(30, ge=1, le=60, description="Simulation duration in days (1 to 60)")
    step_minutes: int = Field(30, ge=5, description="Time step in minutes (minimum 5)")
    observer_height_m: float = Field(0.0, ge=0.0, description="Observer/panel mast height in metres above DEM surface")
    solar_constant_w_m2: float = Field(1361.0, gt=0.0, description="Solar constant at 1 AU in W/m^2 (default 1361.0)")
    panel: Optional[PanelInputsModel] = Field(None, description="Optional solar panel specifications. If omitted, returns illumination opportunity only.")


class DailyEnergyModel(BaseModel):
    date: str = Field(..., description="UTC date (YYYY-MM-DD)")
    energy_wh: float
    energy_kwh: float
    peak_power_w: float
    mean_power_w: float


class ShadowPeriodModel(BaseModel):
    start: str
    end: str
    duration_hours: float


class IlluminationOpportunityModel(BaseModel):
    hours_any_part_lit: float
    hours_fully_lit: float
    hours_shadow: float
    fraction_of_period: float
    number_of_lit_windows: int
    longest_shadow_hours: float
    shortest_lit_window_hours: float
    longest_lit_window_hours: float


class SolarEstimateResponse(BaseModel):
    site_id: str
    site_name: str
    is_placeholder: bool
    label: str = Field("Modelled", description="SRS status label")
    frame: str = "MOON_ME_DE421"
    product_id: str = "lola-dem-75s-240m"
    method: str = "SPICE geometric with terrain horizon from a 240 m DEM and solar irradiance model"
    kernels_used: List[str]
    solar_constant_w_m2: float
    sun_distance_au_factor: Optional[float] = None
    energy_wh: Optional[float] = None
    energy_kwh: Optional[float] = None
    mean_power_w: Optional[float] = None
    peak_power_w: Optional[float] = None
    per_day_energy: List[DailyEnergyModel] = Field(default_factory=list)
    illumination_opportunity: IlluminationOpportunityModel
    shadow_periods: List[ShadowPeriodModel] = Field(default_factory=list)
    message: Optional[str] = None
    assumptions: List[str]
    uncertainty: Dict[str, str]
    disclaimers: List[str]
