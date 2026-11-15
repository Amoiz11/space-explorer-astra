"""
Service for computing terrain-aware solar illumination timelines and windows (LL-14 to LL-16).
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.models import IlluminationResult, CandidateLandingSite
from backend.app.services.dem_service import DEMService, get_dem_service, SiteCoverageError
from backend.app.services.horizon_service import HorizonService, get_horizon_service
from backend.app.services.lunar_geometry_service import (
    LunarGeometryService,
    get_lunar_geometry_service,
    KernelManager,
    FRAME_NAME,
    REQUIRED_KERNELS,
)
from data_pipeline.processors.illumination_processor import (
    IlluminationProcessor,
    parse_iso_timestamp,
)


class IlluminationService:
    """
    Coordinates SPICE solar ephemeris, local terrain horizon profiles,
    and circular segment illumination disk calculations.
    """

    DEFAULT_PRODUCT_ID = "lola-dem-75s-240m"

    def __init__(
        self,
        db: Optional[Session] = None,
        dem_service: Optional[DEMService] = None,
        horizon_service: Optional[HorizonService] = None,
        geometry_service: Optional[LunarGeometryService] = None,
        processor: Optional[IlluminationProcessor] = None,
    ):
        self.db = db
        self.dem_service = dem_service or get_dem_service()
        self.horizon_service = horizon_service or get_horizon_service()
        self.geometry_service = geometry_service or get_lunar_geometry_service()
        self.processor = processor or IlluminationProcessor()

    def calculate_site_illumination(
        self,
        site: CandidateLandingSite,
        start_utc: str,
        days: int = 30,
        step_minutes: int = 30,
        observer_height_m: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Compute terrain-aware illumination series and windows for a candidate landing site.
        """
        # Validate SPICE kernels first
        KernelManager.load_kernels()

        coords = site.coordinates or {}
        values = coords.get("values", [])
        if len(values) < 2:
            raise ValueError(f"Site '{site.id}' coordinates missing [latitude, longitude].")

        lat, lon = float(values[0]), float(values[1])

        # Validate DEM coverage and retrieve site elevation via shared bilinear function
        self.dem_service.validate_coverage(lat)
        site_dem_elev_m = self.dem_service.get_site_elevation(lat, lon)
        total_obs_elev_m = site_dem_elev_m + float(observer_height_m)

        # 1. Compute/retrieve cached 360-degree horizon profile
        horizon_res = self.horizon_service.compute_site_horizon(
            site_lat=lat,
            site_lon=lon,
            azimuth_step_deg=1.0,
            max_distance_km=100.0,
            observer_height_m=observer_height_m,
        )
        horizon_profile = horizon_res["profile"]

        # 2. Compute ephemeris series from SPICE
        geom_res = self.geometry_service.calculate_geometry(
            lat_deg=lat,
            lon_deg=lon,
            elevation_m=total_obs_elev_m,
            start_utc=start_utc,
            days=days,
            step_minutes=step_minutes,
        )
        ephem_series = geom_res["series"]

        # 3. Process terrain-aware illumination with circular segment disk geometry
        illum_res = self.processor.process_illumination_series(
            ephemeris_series=ephem_series,
            horizon_profile=horizon_profile,
            horizon_interp_func=self.horizon_service.interpolate_horizon_elevation,
        )

        # 4. Persist window-level records to DB if session provided
        if self.db is not None:
            self._save_illumination_windows(
                site_id=site.id,
                windows=illum_res["windows"]["any_part_lit"],
                ephem_series=ephem_series,
                params={
                    "start": start_utc,
                    "days": days,
                    "step_minutes": step_minutes,
                    "observer_height_m": observer_height_m,
                },
            )

        return {
            "site_id": site.id,
            "site_name": site.name,
            "is_placeholder": site.is_placeholder,
            "label": "Modelled",
            "frame": FRAME_NAME,
            "product_id": self.DEFAULT_PRODUCT_ID,
            "method": illum_res["method"],
            "observer_elevation_m": round(site_dem_elev_m, 2),
            "observer_height_m": round(observer_height_m, 2),
            "total_observer_elevation_m": round(total_obs_elev_m, 2),
            "kernels_used": REQUIRED_KERNELS,
            "series": illum_res["series"],
            "windows": illum_res["windows"],
            "shadow_periods": illum_res.get("shadow_periods", []),
            "totals": illum_res["totals"],
            "disclaimers": illum_res["disclaimers"],
        }

    def _save_illumination_windows(
        self,
        site_id: str,
        windows: List[Dict[str, Any]],
        ephem_series: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> None:
        """Store window-level illumination results in illumination_results table."""
        try:
            for w in windows:
                dt_start = parse_iso_timestamp(w["start"])
                dt_end = parse_iso_timestamp(w["end"])

                # Estimate mid-window Sun az and el
                sun_az = None
                sun_el = None
                if ephem_series:
                    sun_az = ephem_series[0].get("sun_azimuth_deg")
                    sun_el = ephem_series[0].get("sun_elevation_deg")

                rec = IlluminationResult(
                    site_id=site_id,
                    start_time=dt_start,
                    end_time=dt_end,
                    sun_azimuth=sun_az,
                    sun_elevation=sun_el,
                    illuminated_fraction=1.0,
                    method=self.processor.METHOD_NAME,
                    parameters=params,
                )
                self.db.add(rec)
            self.db.commit()
        except Exception:
            self.db.rollback()


_illumination_service_singleton: Optional[IlluminationService] = None


def get_illumination_service(db: Optional[Session] = None) -> IlluminationService:
    global _illumination_service_singleton
    if db is not None:
        return IlluminationService(db=db)
    if _illumination_service_singleton is None:
        _illumination_service_singleton = IlluminationService()
    return _illumination_service_singleton
