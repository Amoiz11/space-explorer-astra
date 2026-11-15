"""
Landing window comparison service (B5a: LL-27 to LL-30).

For each (site, window) pair computes a row of metrics by reusing existing services:
  - Slope and terrain stats from SlopeService / DEMService
  - Illumination from IlluminationService (terrain horizon, solar disk)
  - Earth visibility from EarthVisibilityService
  - Optional solar energy from SolarPowerService

The site's horizon profile is computed once per site per request (not per time step).
Criteria are user-supplied thresholds labelled "example threshold, not an official
safety criterion". A combined score is never computed unless the user supplies weights.
A site is never labelled "safe".
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.models import CandidateLandingSite
from backend.app.services.dem_service import DEMService, get_dem_service, SiteCoverageError
from backend.app.services.slope_service import SlopeService, get_slope_service
from backend.app.services.illumination_service import IlluminationService, get_illumination_service
from backend.app.services.earth_visibility_service import EarthVisibilityService, get_earth_visibility_service
from backend.app.services.solar_power_service import SolarPowerService, get_solar_power_service
from backend.app.services.lunar_geometry_service import KernelManager, FRAME_NAME, REQUIRED_KERNELS
from backend.app.schemas.lunar_comparison import (
    CompareRequest,
    ComparisonRow,
    IlluminationMetrics,
    EarthMetrics,
    SlopeMetrics,
    ElevationMetrics,
    CriterionResult,
    DataQuality,
    BestBy,
)
from backend.app.schemas.lunar_solar_power import PanelInputsModel

DISCLAIMERS = [
    "Geometric visibility is not a guaranteed radio link.",
    "Sunlight is not guaranteed electrical power.",
    "A 240 m DEM cannot represent terrain smaller than its resolution; real terrain can differ.",
    "Planning support tool, not safety certification.",
    "No site is labelled safe. These metrics support planning only.",
]

METHOD_TEXT = (
    "SPICE DE421 Sun and Earth geometry; LOLA 240 m DEM local horizon (spherical curvature drop, "
    "bilinear interpolation); Horn (1981) slope; illuminated fraction from solar disk / terrain horizon "
    "circular segment geometry. Horizon computed once per site and reused across time steps."
)

SUPPORTED_CRITERIA = {
    "max_mean_slope_deg",
    "min_any_lit_hours",
    "min_earth_visible_hours",
    "min_both_up_hours",
    "max_longest_shadow_hours",
}


def _get_criterion_value(row: ComparisonRow, metric: str) -> float:
    if metric == "max_mean_slope_deg":
        return row.slope.mean_slope_deg
    if metric == "min_any_lit_hours":
        return row.illumination.hours_any_part_lit
    if metric == "min_earth_visible_hours":
        return row.earth.hours_earth_visible
    if metric == "min_both_up_hours":
        return row.hours_both_up
    if metric == "max_longest_shadow_hours":
        return row.illumination.longest_shadow_hours
    raise ValueError(f"Unknown criterion metric: '{metric}'")


def _criterion_passes(metric: str, value: float, threshold: float) -> bool:
    """
    For 'min_*' criteria a pass means value >= threshold.
    For 'max_*' criteria a pass means value <= threshold.
    """
    if metric.startswith("min_"):
        return value >= threshold
    if metric.startswith("max_"):
        return value <= threshold
    return False


class LandingWindowService:
    """
    Coordinates existing services to build per-(site, window) comparison rows.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        dem_service: Optional[DEMService] = None,
        slope_service: Optional[SlopeService] = None,
        illum_service: Optional[IlluminationService] = None,
        earth_service: Optional[EarthVisibilityService] = None,
        solar_service: Optional[SolarPowerService] = None,
    ):
        self.db = db
        self.dem_service = dem_service or get_dem_service()
        self.slope_service = slope_service or get_slope_service()
        self.illum_service = illum_service or get_illumination_service(db)
        self.earth_service = earth_service or get_earth_visibility_service(db)
        self.solar_service = solar_service or (get_solar_power_service(db) if db else None)

    def _get_slope_metrics(
        self,
        site: CandidateLandingSite,
        lat: float,
        lon: float,
    ) -> Tuple[SlopeMetrics, ElevationMetrics]:
        """Extract slope and elevation statistics from the DEM."""
        radius = site.analysis_radius_m or 1000.0
        stats = self.slope_service.analyze_site(lat=lat, lon=lon, analysis_radius_m=radius)

        # Stats are nested: stats["slope"]["mean_deg"], stats["elevation"]["mean_m"], etc.
        slope_block = stats.get("slope", {})
        elev_block = stats.get("elevation", {})

        mean_slope = round(float(slope_block.get("mean_deg", 0.0)), 3)
        max_slope = round(float(slope_block.get("max_deg", 0.0)), 3)
        p90 = round(float(slope_block.get("p90_deg", 0.0)), 3)

        mean_elev = round(float(elev_block.get("mean_m", 0.0)), 2)
        relief = round(float(elev_block.get("local_relief_m", 0.0)), 2)

        return (
            SlopeMetrics(mean_slope_deg=mean_slope, max_slope_deg=max_slope, p90_slope_deg=p90),
            ElevationMetrics(mean_elevation_m=mean_elev, relief_m=relief),
        )

    def _build_row(
        self,
        site: CandidateLandingSite,
        window: Any,
        step_minutes: int,
        observer_height_m: float,
        panel: Optional[PanelInputsModel],
        lat: float,
        lon: float,
        obs_elev_m: float,
        slope_m: SlopeMetrics,
        elev_m: ElevationMetrics,
    ) -> ComparisonRow:
        """Build one ComparisonRow for a given (site, window)."""
        start = window.start
        days = window.days

        # --- Illumination (horizon computed once inside, cached by horizon_service) ---
        illum_res = self.illum_service.calculate_site_illumination(
            site=site,
            start_utc=start,
            days=days,
            step_minutes=step_minutes,
            observer_height_m=observer_height_m,
        )
        illum_totals = illum_res.get("totals", {})

        illum_metrics = IlluminationMetrics(
            hours_any_part_lit=round(float(illum_totals.get("hours_any_part_lit", 0.0)), 2),
            hours_fully_lit=round(float(illum_totals.get("hours_fully_lit", 0.0)), 2),
            hours_shadow=round(float(illum_totals.get("hours_shadow", 0.0)), 2),
            longest_shadow_hours=round(float(illum_totals.get("longest_continuous_shadow_hours", 0.0)), 2),
            number_of_lit_windows=int(illum_totals.get("number_of_windows", 0)),
        )

        # --- Earth visibility ---
        earth_res = self.earth_service.calculate_site_earth_visibility(
            site=site,
            start_utc=start,
            days=days,
            step_minutes=step_minutes,
            observer_height_m=observer_height_m,
            earth_disk="center",
        )
        earth_totals = earth_res.get("totals", {})

        earth_metrics = EarthMetrics(
            hours_earth_visible=round(float(earth_totals.get("earth_visible_hours", 0.0)), 2),
            hours_earth_blocked=round(
                float(earth_totals.get("blocked_by_terrain_hours", 0.0))
                + float(earth_totals.get("below_horizon_hours", 0.0)),
                2,
            ),
            number_of_earth_windows=int(earth_totals.get("number_of_windows", 0)),
        )

        # --- Both Sun and Earth above horizon ---
        # Count steps where illuminated_fraction > 0 AND earth obstruction == "clear"
        illum_series = illum_res.get("series", [])
        earth_series = earth_res.get("series", [])
        step_hours = step_minutes / 60.0
        both_up_steps = 0
        for illum_pt, earth_pt in zip(illum_series, earth_series):
            sun_up = illum_pt.get("illuminated_fraction", 0.0) > 0.0
            earth_up = earth_pt.get("obstruction_status", "blocked") == "clear"
            if sun_up and earth_up:
                both_up_steps += 1
        raw_both_up = round(both_up_steps * step_hours, 2)
        # Overlap cannot exceed either sunlit or Earth visible totals
        hours_both_up = round(
            min(raw_both_up, illum_metrics.hours_any_part_lit, earth_metrics.hours_earth_visible),
            2,
        )

        # --- Optional solar energy ---
        energy_kwh: Optional[float] = None
        if panel is not None and self.solar_service is not None:
            solar_res = self.solar_service.estimate_solar_power(
                site=site,
                start_utc=start,
                days=days,
                step_minutes=step_minutes,
                observer_height_m=observer_height_m,
                panel=panel,
            )
            energy_kwh = solar_res.get("energy_kwh")

        return ComparisonRow(
            site_id=site.id,
            site_name=site.name or "",
            is_placeholder=bool(site.is_placeholder),
            window_start=start,
            window_days=days,
            observer_elevation_m=round(obs_elev_m, 2),
            illumination=illum_metrics,
            earth=earth_metrics,
            slope=slope_m,
            elevation=elev_m,
            hours_both_up=hours_both_up,
            energy_kwh=round(energy_kwh, 4) if energy_kwh is not None else None,
            criteria_results=[],
            data_quality=DataQuality(
                dem_resolution_m=240,
                is_placeholder=bool(site.is_placeholder),
                kernels_used=list(REQUIRED_KERNELS),
                horizon_type="terrain",
                notes=[
                    "240 m DEM cannot represent sub-resolution ridges, boulders, or micro-terrain.",
                    "Illuminated fraction uses circular segment geometry (uniform solar disk).",
                    "Earth visibility uses geometric line-of-sight; relay satellites are not modelled.",
                    "Site is never labelled safe. These metrics support planning only.",
                ],
            ),
        )

    def compute_comparison(
        self,
        sites: List[CandidateLandingSite],
        request: CompareRequest,
    ) -> Dict[str, Any]:
        """
        Run all (site, window) combinations, evaluate criteria, pick best_by.
        Returns a dict ready for the response.
        """
        KernelManager.load_kernels()

        t0 = time.perf_counter()

        # Convert panel schema if supplied
        panel_model: Optional[PanelInputsModel] = None
        if request.panel is not None:
            p = request.panel
            panel_model = PanelInputsModel(
                panel_area_m2=p.panel_area_m2,
                efficiency=p.efficiency,
                tilt_deg=p.tilt_deg,
                panel_azimuth_deg=p.panel_azimuth_deg,
                track_sun_azimuth=p.track_sun_azimuth,
            )

        # Pre-compute slope/elevation once per site (DEM-only, no kernels)
        site_slope_cache: Dict[str, Tuple[SlopeMetrics, ElevationMetrics]] = {}
        site_latlon_cache: Dict[str, Tuple[float, float]] = {}
        site_elev_cache: Dict[str, float] = {}

        for site in sites:
            coords = site.coordinates or {}
            values = coords.get("values", [])
            lat, lon = float(values[0]), float(values[1])
            site_latlon_cache[site.id] = (lat, lon)

            self.dem_service.validate_coverage(lat)
            obs_elev = self.dem_service.get_site_elevation(lat, lon)
            site_elev_cache[site.id] = obs_elev

            if site.id not in site_slope_cache:
                slope_m, elev_m = self._get_slope_metrics(site, lat, lon)
                site_slope_cache[site.id] = (slope_m, elev_m)

        # Build all rows
        rows: List[ComparisonRow] = []
        for site in sites:
            lat, lon = site_latlon_cache[site.id]
            obs_elev = site_elev_cache[site.id]
            slope_m, elev_m = site_slope_cache[site.id]

            for window in request.windows:
                row = self._build_row(
                    site=site,
                    window=window,
                    step_minutes=request.step_minutes,
                    observer_height_m=request.observer_height_m,
                    panel=panel_model,
                    lat=lat,
                    lon=lon,
                    obs_elev_m=obs_elev,
                    slope_m=slope_m,
                    elev_m=elev_m,
                )
                rows.append(row)

        # Evaluate criteria
        criteria_list = request.criteria or []
        for row in rows:
            crit_results = []
            for crit in criteria_list:
                try:
                    val = _get_criterion_value(row, crit.metric)
                    passed = _criterion_passes(crit.metric, val, crit.threshold)
                except ValueError:
                    val = float("nan")
                    passed = False
                crit_results.append(CriterionResult(
                    metric=crit.metric,
                    threshold=crit.threshold,
                    label=crit.label,
                    value=round(val, 3),
                    passed=passed,
                ))
            row.criteria_results = crit_results

        # Compute best_by (key = "site_id:window_start")
        def row_key(r: ComparisonRow) -> str:
            return f"{r.site_id}:{r.window_start}"

        best_sunlight = max(rows, key=lambda r: r.illumination.hours_any_part_lit) if rows else None
        best_earth = max(rows, key=lambda r: r.earth.hours_earth_visible) if rows else None
        lowest_slope = min(rows, key=lambda r: r.slope.mean_slope_deg) if rows else None
        most_both = max(rows, key=lambda r: r.hours_both_up) if rows else None

        best_by = BestBy(
            best_for_sunlight=row_key(best_sunlight) if best_sunlight else None,
            best_for_earth_visibility=row_key(best_earth) if best_earth else None,
            lowest_slope=row_key(lowest_slope) if lowest_slope else None,
            most_hours_both_up=row_key(most_both) if most_both else None,
        )

        elapsed = round(time.perf_counter() - t0, 2)

        return {
            "rows": rows,
            "best_by": best_by,
            "criteria": criteria_list,
            "elapsed_seconds": elapsed,
        }


_landing_window_service_singleton: Optional[LandingWindowService] = None


def get_landing_window_service(db: Optional[Session] = None) -> LandingWindowService:
    global _landing_window_service_singleton
    if db is not None:
        return LandingWindowService(db=db)
    if _landing_window_service_singleton is None:
        _landing_window_service_singleton = LandingWindowService()
    return _landing_window_service_singleton
