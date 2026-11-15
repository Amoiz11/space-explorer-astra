"""
Solar power opportunity and generation estimation service (LL-23 to LL-26).
"""

import math
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import numpy as np

from backend.app.models.models import SolarPowerEstimate, CandidateLandingSite
from backend.app.services.dem_service import DEMService, get_dem_service, SiteCoverageError
from backend.app.services.illumination_service import (
    IlluminationService,
    get_illumination_service,
)
from backend.app.services.lunar_geometry_service import KernelManager, FRAME_NAME, REQUIRED_KERNELS
from backend.app.schemas.lunar_solar_power import PanelInputsModel

# Standard astronomical unit in km (IAU definition)
AU_KM = 149597870.7
DEFAULT_SOLAR_CONSTANT_W_M2 = 1361.0

ASSUMPTIONS_LIST = [
    "No atmosphere: Lunar surface is a hard vacuum with zero atmospheric absorption, extinction, or scattering.",
    "No reflected or scattered light: Direct solar beam only; secondary terrain albedo reflectance is ignored.",
    "No panel degradation: Photovoltaic conversion efficiency is assumed constant with no radiation, micrometeorite, or dust degradation.",
    "No temperature effect: Efficiency derating due to extreme lunar cryogenic and noon surface temperatures is not modelled.",
    "No batteries or electrical loads: Energy calculation represents raw direct generation potential without battery storage dynamics or curtailment.",
    "Point-like panel: Uniform illumination and geometric orientation across the panel surface.",
    "Direct beam only with solar disk approximation: Irradiance scales with the illuminated solar disk fraction (uniform disk brightness, limb darkening ignored).",
]

UNCERTAINTY_DICT = {
    "terrain_resolution": "The 240 m LOLA DEM cannot resolve boulders, mounds, or micro-topography smaller than 240 m, which can cause local shadows or altered sunrise/sunset times.",
    "solar_disk_approximation": "Illuminated fraction uses circular segment geometry assuming uniform solar disk brightness rather than realistic limb darkening.",
    "ignored_reflected_light": "Ignoring secondary terrain reflections (albedo) underestimates available diffuse irradiance, especially near steep illuminated slopes or crater rims.",
    "solar_constant_choice": "Solar irradiance assumes standard solar constant of 1361 W/m^2 at 1 AU scaled by inverse-square distance from DE421 ephemeris; natural solar cycle variations are not included.",
}

DISCLAIMERS_LIST = [
    "Sunlight is not guaranteed electrical power.",
    "Planning support tool, not safety certification.",
    "Direct beam potential only; actual power system performance requires thermal, regolith dust, and battery-load modeling.",
]


def calculate_panel_normal_enu(tilt_deg: float, panel_azimuth_deg: float) -> np.ndarray:
    """
    Compute panel normal unit vector in local East-North-Up (ENU) coordinates.
    tilt_deg: 0 = horizontal (normal pointing Up), 90 = vertical.
    panel_azimuth_deg: azimuth clockwise from North toward East.
    """
    beta_rad = math.radians(tilt_deg)
    az_rad = math.radians(panel_azimuth_deg)

    # In ENU:
    # E = sin(beta) * sin(az)
    # N = sin(beta) * cos(az)
    # U = cos(beta)
    e = math.sin(beta_rad) * math.sin(az_rad)
    n = math.sin(beta_rad) * math.cos(az_rad)
    u = math.cos(beta_rad)
    return np.array([e, n, u], dtype=np.float64)


def calculate_sun_vector_enu(sun_azimuth_deg: float, sun_elevation_deg: float) -> np.ndarray:
    """
    Compute Sun direction unit vector in local East-North-Up (ENU) coordinates.
    """
    az_rad = math.radians(sun_azimuth_deg)
    el_rad = math.radians(sun_elevation_deg)

    e = math.cos(el_rad) * math.sin(az_rad)
    n = math.cos(el_rad) * math.cos(az_rad)
    u = math.sin(el_rad)
    return np.array([e, n, u], dtype=np.float64)


def compute_incidence_cos(
    sun_az_deg: float,
    sun_el_deg: float,
    tilt_deg: float,
    panel_az_deg: float,
    track_sun_azimuth: bool = False,
) -> float:
    """
    Calculate cos(theta_inc) between panel normal and Sun vector.
    Never returns negative (backside of panel cannot receive direct front illumination).
    """
    effective_az = sun_az_deg if track_sun_azimuth else panel_az_deg
    beta_rad = math.radians(tilt_deg)
    el_rad = math.radians(sun_el_deg)
    d_az_rad = math.radians(sun_az_deg - effective_az)

    # cos(inc) = sin(beta)*cos(el)*cos(az_sun - az_panel) + cos(beta)*sin(el)
    cos_inc = math.sin(beta_rad) * math.cos(el_rad) * math.cos(d_az_rad) + math.cos(beta_rad) * math.sin(el_rad)
    return max(0.0, float(cos_inc))


class SolarPowerService:
    """
    Computes solar irradiance and power estimates by coupling
    SPICE solar ephemeris, DEM local terrain horizon profiles,
    and panel geometric orientation.
    """

    DEFAULT_PRODUCT_ID = "lola-dem-75s-240m"

    def __init__(
        self,
        db: Optional[Session] = None,
        dem_service: Optional[DEMService] = None,
        illum_service: Optional[IlluminationService] = None,
    ):
        self.db = db
        self.dem_service = dem_service or get_dem_service()
        self.illum_service = illum_service or get_illumination_service(db)

    def estimate_solar_power(
        self,
        site: CandidateLandingSite,
        start_utc: str,
        days: int = 30,
        step_minutes: int = 30,
        observer_height_m: float = 0.0,
        solar_constant_w_m2: float = DEFAULT_SOLAR_CONSTANT_W_M2,
        panel: Optional[PanelInputsModel] = None,
    ) -> Dict[str, Any]:
        """
        Compute solar power and energy estimate or illumination opportunity.
        """
        # Ensure SPICE kernels loaded
        KernelManager.load_kernels()

        # Retrieve illumination results (reuses cached horizon profile)
        illum_res = self.illum_service.calculate_site_illumination(
            site=site,
            start_utc=start_utc,
            days=days,
            step_minutes=step_minutes,
            observer_height_m=observer_height_m,
        )

        series = illum_res.get("series", [])
        totals = illum_res.get("totals", {})
        shadow_periods = illum_res.get("shadow_periods", [])

        # Build illumination opportunity object
        total_sim_hours = totals.get("total_simulation_hours", days * 24.0)
        hours_lit = totals.get("hours_any_part_lit", 0.0)
        frac_period = round(hours_lit / total_sim_hours, 4) if total_sim_hours > 0 else 0.0

        illum_opportunity = {
            "hours_any_part_lit": totals.get("hours_any_part_lit", 0.0),
            "hours_fully_lit": totals.get("hours_fully_lit", 0.0),
            "hours_shadow": totals.get("hours_shadow", 0.0),
            "fraction_of_period": frac_period,
            "number_of_lit_windows": totals.get("number_of_windows", 0),
            "longest_shadow_hours": totals.get("longest_continuous_shadow_hours", 0.0),
            "shortest_lit_window_hours": totals.get("shortest_window_hours", 0.0),
            "longest_lit_window_hours": totals.get("longest_window_hours", 0.0),
        }

        # Calculate representative Sun-Moon distance factor (1 AU / D)^2
        dist_factors = []
        for pt in series:
            d_km = pt.get("sun_distance_km")
            if d_km and d_km > 0:
                dist_factors.append((AU_KM / d_km) ** 2)
            else:
                dist_factors.append(1.0)
        mean_dist_factor = round(float(np.mean(dist_factors)), 6) if dist_factors else 1.0

        # Case 1: No panel inputs given (LL-26)
        if panel is None:
            result = {
                "site_id": site.id,
                "site_name": site.name,
                "is_placeholder": site.is_placeholder,
                "label": "Modelled",
                "frame": FRAME_NAME,
                "product_id": self.DEFAULT_PRODUCT_ID,
                "method": "SPICE geometric with terrain horizon from a 240 m DEM and solar irradiance model",
                "kernels_used": REQUIRED_KERNELS,
                "solar_constant_w_m2": solar_constant_w_m2,
                "sun_distance_au_factor": mean_dist_factor,
                "energy_wh": None,
                "energy_kwh": None,
                "mean_power_w": None,
                "peak_power_w": None,
                "per_day_energy": [],
                "illumination_opportunity": illum_opportunity,
                "shadow_periods": shadow_periods,
                "message": "Panel inputs (area, efficiency, tilt) are required to compute energy generation. Returning illumination opportunity only (LL-26).",
                "assumptions": ASSUMPTIONS_LIST,
                "uncertainty": UNCERTAINTY_DICT,
                "disclaimers": DISCLAIMERS_LIST,
            }

            self._save_estimate(
                site_id=site.id,
                time_range={"start": start_utc, "days": days, "step_minutes": step_minutes},
                panel_assumptions=None,
                estimated_energy=None,
                units=None,
                uncertainty=UNCERTAINTY_DICT,
            )
            return result

        # Case 2: Panel inputs provided -> compute irradiance and energy
        step_hours = step_minutes / 60.0
        area = panel.panel_area_m2
        eff = panel.efficiency
        tilt = panel.tilt_deg
        az_panel = panel.panel_azimuth_deg
        track = panel.track_sun_azimuth

        powers_w: List[float] = []
        daily_groups: Dict[str, List[float]] = {}

        for i, pt in enumerate(series):
            ts = pt["timestamp"]
            date_key = ts[:10]  # YYYY-MM-DD
            sun_az = pt.get("sun_azimuth", pt.get("sun_azimuth_deg", 0.0))
            sun_el = pt.get("sun_elevation", pt.get("sun_elevation_deg", 0.0))
            frac_lit = pt.get("illuminated_fraction", 0.0)
            fac = dist_factors[i] if i < len(dist_factors) else 1.0

            cos_inc = compute_incidence_cos(
                sun_az_deg=sun_az,
                sun_el_deg=sun_el,
                tilt_deg=tilt,
                panel_az_deg=az_panel,
                track_sun_azimuth=track,
            )

            # Direct solar irradiance on panel front surface
            irradiance_w_m2 = solar_constant_w_m2 * fac * cos_inc * frac_lit
            power_w = irradiance_w_m2 * area * eff
            powers_w.append(power_w)

            if date_key not in daily_groups:
                daily_groups[date_key] = []
            daily_groups[date_key].append(power_w)

        # Total energy in Wh
        total_energy_wh = float(np.sum(powers_w) * step_hours)
        total_energy_kwh = total_energy_wh / 1000.0
        peak_power_w = float(np.max(powers_w)) if powers_w else 0.0
        mean_power_w = (total_energy_wh / total_sim_hours) if total_sim_hours > 0 else 0.0

        # Construct daily breakdown
        per_day_list = []
        for date_str, p_list in daily_groups.items():
            day_wh = float(np.sum(p_list) * step_hours)
            day_hours = len(p_list) * step_hours
            day_mean = (day_wh / day_hours) if day_hours > 0 else 0.0
            per_day_list.append({
                "date": date_str,
                "energy_wh": round(day_wh, 2),
                "energy_kwh": round(day_wh / 1000.0, 4),
                "peak_power_w": round(float(np.max(p_list)), 2),
                "mean_power_w": round(day_mean, 2),
            })

        panel_dict = {
            "panel_area_m2": area,
            "efficiency": eff,
            "tilt_deg": tilt,
            "panel_azimuth_deg": az_panel,
            "track_sun_azimuth": track,
            "solar_constant_w_m2": solar_constant_w_m2,
        }

        self._save_estimate(
            site_id=site.id,
            time_range={"start": start_utc, "days": days, "step_minutes": step_minutes},
            panel_assumptions=panel_dict,
            estimated_energy=round(total_energy_wh, 2),
            units="Wh",
            uncertainty=UNCERTAINTY_DICT,
        )

        return {
            "site_id": site.id,
            "site_name": site.name,
            "is_placeholder": site.is_placeholder,
            "label": "Modelled",
            "frame": FRAME_NAME,
            "product_id": self.DEFAULT_PRODUCT_ID,
            "method": "SPICE geometric with terrain horizon from a 240 m DEM and solar irradiance model",
            "kernels_used": REQUIRED_KERNELS,
            "solar_constant_w_m2": solar_constant_w_m2,
            "sun_distance_au_factor": mean_dist_factor,
            "energy_wh": round(total_energy_wh, 2),
            "energy_kwh": round(total_energy_kwh, 4),
            "mean_power_w": round(mean_power_w, 2),
            "peak_power_w": round(peak_power_w, 2),
            "per_day_energy": per_day_list,
            "illumination_opportunity": illum_opportunity,
            "shadow_periods": shadow_periods,
            "message": None,
            "assumptions": ASSUMPTIONS_LIST,
            "uncertainty": UNCERTAINTY_DICT,
            "disclaimers": DISCLAIMERS_LIST,
        }

    def _save_estimate(
        self,
        site_id: str,
        time_range: Dict[str, Any],
        panel_assumptions: Optional[Dict[str, Any]],
        estimated_energy: Optional[float],
        units: Optional[str],
        uncertainty: Dict[str, Any],
    ) -> None:
        """Store request and estimate in solar_power_estimates table."""
        if self.db is None:
            return
        try:
            rec = SolarPowerEstimate(
                site_id=site_id,
                time_range=time_range,
                panel_assumptions=panel_assumptions,
                estimated_energy=estimated_energy,
                units=units,
                uncertainty=uncertainty,
            )
            self.db.add(rec)
            self.db.commit()
        except Exception:
            self.db.rollback()


_solar_power_service_singleton: Optional[SolarPowerService] = None


def get_solar_power_service(db: Optional[Session] = None) -> SolarPowerService:
    global _solar_power_service_singleton
    if db is not None:
        return SolarPowerService(db=db)
    if _solar_power_service_singleton is None:
        _solar_power_service_singleton = SolarPowerService()
    return _solar_power_service_singleton
