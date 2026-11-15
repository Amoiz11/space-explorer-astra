"""
Slope service for computing slope and morphologic metrics over landing sites.
"""

from typing import Dict, Any, Optional
import numpy as np

from data_pipeline.processors.slope_processor import SlopeProcessor
from backend.app.services.dem_service import DEMService, get_dem_service


class SlopeService:
    """
    Coordinates DEM extraction and slope metric computation for landing footprints.
    """

    def __init__(self, dem_service: Optional[DEMService] = None, slope_processor: Optional[SlopeProcessor] = None):
        self.dem_service = dem_service or get_dem_service()
        self.processor = slope_processor or SlopeProcessor(pixel_spacing_m=240.0)

    def analyze_site(
        self,
        lat: float,
        lon: float,
        analysis_radius_m: float = 1000.0,
        semi_major_m: Optional[float] = None,
        semi_minor_m: Optional[float] = None,
        orientation_deg: Optional[float] = None,
        criteria: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate site coverage, extract DEM elevation and slope in landing footprint,
        and return complete metrics dictionary.
        """
        # Validate coverage and find center pixel
        _, _, center_row, center_col = self.dem_service.latlon_to_grid_indices(lat, lon)

        elev_full = self.dem_service.get_elevation_array()
        rows, cols = elev_full.shape

        # Compute bounding box with margin
        max_dim = max(semi_major_m or analysis_radius_m, semi_minor_m or analysis_radius_m, analysis_radius_m)
        r_pix = int(np.ceil(max_dim / self.processor.pixel_spacing_m)) + 4

        r_min = max(0, center_row - r_pix)
        r_max = min(rows, center_row + r_pix + 1)
        c_min = max(0, center_col - r_pix)
        c_max = min(cols, center_col + r_pix + 1)

        # Slice sub-grid
        sub_elev = np.array(elev_full[r_min:r_max, c_min:c_max], dtype=np.float64)

        # Compute slope on sub-grid using Horn
        sub_slope = self.processor.compute_slope_grid(sub_elev)

        # Compute mask within sub-grid
        sub_center_r = float(center_row - r_min)
        sub_center_c = float(center_col - c_min)
        sub_mask = self.processor.get_ellipse_mask(
            grid_shape=sub_elev.shape,
            center_row=sub_center_r,
            center_col=sub_center_c,
            semi_major_m=semi_major_m,
            semi_minor_m=semi_minor_m,
            orientation_deg=orientation_deg,
            analysis_radius_m=analysis_radius_m,
        )

        # Compute statistics
        stats = self.processor.compute_terrain_statistics(
            elev_grid=sub_elev,
            slope_grid=sub_slope,
            mask=sub_mask,
            criteria=criteria,
        )
        return stats


_slope_service_singleton: Optional[SlopeService] = None


def get_slope_service() -> SlopeService:
    global _slope_service_singleton
    if _slope_service_singleton is None:
        _slope_service_singleton = SlopeService()
    return _slope_service_singleton
