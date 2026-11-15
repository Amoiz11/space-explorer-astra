"""
Horizon service coordinating DEM extraction and horizon profile generation (Phase B3b).
"""

from typing import Optional, Dict, Any, List
import numpy as np

from data_pipeline.processors.horizon_processor import HorizonProcessor, MOON_RADIUS_M, MAP_SCALE_M
from backend.app.services.dem_service import DEMService, get_dem_service, SiteCoverageError
from backend.app.schemas.lunar_horizon import (
    HorizonProfileResponse,
    HorizonSummaryModel,
    HorizonPointModel,
)


class HorizonService:
    """
    Coordinates local terrain horizon computation from the LOLA polar DEM.
    """

    DEFAULT_PRODUCT_ID = "lola-dem-75s-240m"
    DEFAULT_RESOLUTION = "240 m/pixel (240.0 m/pix, true at south pole)"

    def __init__(
        self,
        dem_service: Optional[DEMService] = None,
        processor: Optional[HorizonProcessor] = None,
    ):
        self.dem_service = dem_service or get_dem_service()
        self.processor = processor or HorizonProcessor(
            moon_radius_m=MOON_RADIUS_M,
            map_scale_m=MAP_SCALE_M,
        )
        self._cache: Dict[Tuple[float, float, float, float, float], Dict[str, Any]] = {}

    def compute_site_horizon(
        self,
        site_lat: float,
        site_lon: float,
        azimuth_step_deg: float = 1.0,
        max_distance_km: float = 100.0,
        observer_height_m: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Validate site coverage, sample DEM, and compute the 360-degree horizon profile.
        Caches profile in-memory per site and parameter combination.
        Raises SiteCoverageError if site is north of -75°S.
        """
        key = (
            round(float(site_lat), 6),
            round(float(site_lon), 6),
            round(float(azimuth_step_deg), 4),
            round(float(max_distance_km), 3),
            round(float(observer_height_m), 3),
        )
        if key in self._cache:
            return self._cache[key]

        # Validate DEM coverage (raises SiteCoverageError if lat > -75.0)
        self.dem_service.validate_coverage(site_lat)

        sample_i, line_j = self.dem_service.processor.latlon_to_pixel(site_lat, site_lon)
        # Convert 1-based DSMAP pixel to 0-based numpy row, col
        site_row = line_j - 1.0
        site_col = sample_i - 1.0

        elev_array = self.dem_service.get_elevation_array()

        result = self.processor.compute_horizon_profile(
            elev_array=elev_array,
            site_row=site_row,
            site_col=site_col,
            site_lon_deg=site_lon,
            site_lat_deg=site_lat,
            azimuth_step_deg=azimuth_step_deg,
            max_distance_km=max_distance_km,
            observer_height_m=observer_height_m,
        )

        self._cache[key] = result
        return result

    @staticmethod
    def interpolate_horizon_elevation(profile: List[Dict[str, Any]], azimuth_deg: float) -> float:
        """
        Linearly interpolate horizon elevation at an arbitrary target azimuth [0, 360)
        from a profile list of {"azimuth_deg": ..., "horizon_elevation_deg": ...}.
        """
        az = float(azimuth_deg) % 360.0
        if not profile:
            return 0.0

        az_list = [p["azimuth_deg"] for p in profile]
        el_list = [p["horizon_elevation_deg"] for p in profile]

        # Use np.interp with periodic boundary wrap-around
        # Extend with 360.0 matching az 0.0
        az_extended = np.array(az_list + [360.0])
        el_extended = np.array(el_list + [el_list[0]])

        interp_el = float(np.interp(az, az_extended, el_extended))
        return round(interp_el, 4)


_horizon_service_singleton: Optional[HorizonService] = None


def get_horizon_service() -> HorizonService:
    global _horizon_service_singleton
    if _horizon_service_singleton is None:
        _horizon_service_singleton = HorizonService()
    return _horizon_service_singleton
