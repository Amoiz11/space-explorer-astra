"""
Service for computing direct-to-Earth line-of-sight visibility timelines and windows (LL-19 to LL-22).
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.models import EarthVisibilityWindow, CandidateLandingSite
from backend.app.services.dem_service import DEMService, get_dem_service, SiteCoverageError
from backend.app.services.horizon_service import HorizonService, get_horizon_service
from backend.app.services.lunar_geometry_service import (
    LunarGeometryService,
    get_lunar_geometry_service,
    KernelManager,
    FRAME_NAME,
    REQUIRED_KERNELS,
)
from data_pipeline.processors.earth_visibility_processor import (
    EarthVisibilityProcessor,
    parse_iso_timestamp,
)


class EarthVisibilityService:
    """
    Coordinates SPICE Earth ephemeris, local terrain horizon profiles,
    and line-of-sight obstruction calculations.
    """

    DEFAULT_PRODUCT_ID = "lola-dem-75s-240m"

    def __init__(
        self,
        db: Optional[Session] = None,
        dem_service: Optional[DEMService] = None,
        horizon_service: Optional[HorizonService] = None,
        geometry_service: Optional[LunarGeometryService] = None,
        processor: Optional[EarthVisibilityProcessor] = None,
    ):
        self.db = db
        self.dem_service = dem_service or get_dem_service()
        self.horizon_service = horizon_service or get_horizon_service()
        self.geometry_service = geometry_service or get_lunar_geometry_service()
        self.processor = processor or EarthVisibilityProcessor()

    def calculate_site_earth_visibility(
        self,
        site: CandidateLandingSite,
        start_utc: str,
        days: int = 30,
        step_minutes: int = 30,
        observer_height_m: float = 0.0,
        earth_disk: str = "center",
    ) -> Dict[str, Any]:
        """
        Compute direct-to-Earth line-of-sight visibility series and windows for a candidate landing site.
        """
        # Validate SPICE kernels first
        KernelManager.load_kernels()

        if earth_disk not in ("center", "upper_limb"):
            raise ValueError(f"Invalid earth_disk: '{earth_disk}'. Must be 'center' or 'upper_limb'.")

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

        # 3. Process Earth visibility
        vis_res = self.processor.process_visibility_series(
            ephemeris_series=ephem_series,
            horizon_profile=horizon_profile,
            horizon_interp_func=self.horizon_service.interpolate_horizon_elevation,
            earth_disk=earth_disk,
        )

        # 4. Persist window-level records to DB if session provided
        if self.db is not None:
            self._save_earth_visibility_windows(
                site_id=site.id,
                windows=vis_res["windows"],
                params={
                    "start": start_utc,
                    "days": days,
                    "step_minutes": step_minutes,
                    "observer_height_m": observer_height_m,
                    "earth_disk": earth_disk,
                },
            )

        return {
            "site_id": site.id,
            "site_name": site.name,
            "is_placeholder": site.is_placeholder,
            "label": "Modelled",
            "frame": FRAME_NAME,
            "product_id": self.DEFAULT_PRODUCT_ID,
            "method": vis_res["method"],
            "observer_elevation_m": round(site_dem_elev_m, 2),
            "observer_height_m": round(observer_height_m, 2),
            "total_observer_elevation_m": round(total_obs_elev_m, 2),
            "kernels_used": REQUIRED_KERNELS,
            "earth_disk_criterion": earth_disk,
            "series": vis_res["series"],
            "windows": vis_res["windows"],
            "totals": vis_res["totals"],
            "relay_communication": vis_res["relay_communication"],
            "relay_communication_note": vis_res["relay_communication_note"],
            "disclaimers": vis_res["disclaimers"],
        }

    def _save_earth_visibility_windows(
        self,
        site_id: str,
        windows: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> None:
        """Store window-level visibility results in earth_visibility_windows table."""
        try:
            for w in windows:
                dt_start = parse_iso_timestamp(w["start"])
                dt_end = parse_iso_timestamp(w["end"])

                rec = EarthVisibilityWindow(
                    site_id=site_id,
                    start_time=dt_start,
                    end_time=dt_end,
                    earth_azimuth=w.get("mean_earth_azimuth"),
                    earth_elevation=w.get("mean_earth_elevation"),
                    obstruction_status="clear",
                    parameters=params,
                )
                self.db.add(rec)
            self.db.commit()
        except Exception:
            self.db.rollback()


_earth_visibility_service_singleton: Optional[EarthVisibilityService] = None


def get_earth_visibility_service(db: Optional[Session] = None) -> EarthVisibilityService:
    global _earth_visibility_service_singleton
    if db is not None:
        return EarthVisibilityService(db=db)
    if _earth_visibility_service_singleton is None:
        _earth_visibility_service_singleton = EarthVisibilityService()
    return _earth_visibility_service_singleton
