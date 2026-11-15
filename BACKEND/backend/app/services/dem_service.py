"""
DEM service for loading, caching, and sampling lunar terrain elevation.
"""

import os
import math
from typing import Optional, Tuple, Dict, Any
import numpy as np

from data_pipeline.processors.lunar_coordinate_processor import (
    LunarCoordinateProcessor,
    UnsupportedProjectionError,
)

DEFAULT_DEM_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "storage", "processed", "lunar", "ldem_75s_240m_elev.npy"
)

# Label parameters from LOLA LDEM_75S_240M
DEFAULT_LABEL_PARAMS: Dict[str, Any] = {
    "map_scale": 240.0,
    "lines": 3812,
    "line_samples": 3812,
    "center_latitude": -90.0,
    "sphere_radius_m": 1737400.0,
    "minimum_latitude": -90.0,
    "maximum_latitude": -75.0,
}


class SiteCoverageError(ValueError):
    """Raised when a candidate landing site falls outside DEM coverage."""
    pass


class DEMService:
    """
    Service for accessing LOLA DEM data and coordinate transformations.
    Caches the in-memory array and coordinate processor.
    """

    _instance: Optional["DEMService"] = None

    def __init__(
        self,
        dem_path: Optional[str] = None,
        label_params: Optional[Dict[str, Any]] = None,
        elev_array: Optional[np.ndarray] = None,
    ):
        self.dem_path = dem_path or DEFAULT_DEM_PATH
        self.label_params = label_params or DEFAULT_LABEL_PARAMS
        self._elev_array: Optional[np.ndarray] = elev_array
        self._processor: Optional[LunarCoordinateProcessor] = None

    @property
    def processor(self) -> LunarCoordinateProcessor:
        if self._processor is None:
            self._processor = LunarCoordinateProcessor(self.label_params)
        return self._processor

    def get_elevation_array(self) -> np.ndarray:
        """Get or load the 2D elevation array."""
        if self._elev_array is None:
            if not os.path.exists(self.dem_path):
                raise FileNotFoundError(
                    f"Processed DEM file not found at {self.dem_path}. "
                    "Ensure Phase B1 DEM pipeline has been run."
                )
            self._elev_array = np.load(self.dem_path, mmap_mode="r")
        return self._elev_array

    def validate_coverage(self, lat: float) -> None:
        """
        Verify that latitude falls inside south-polar DEM coverage [-90, -75] deg.
        Raises SiteCoverageError if outside.
        """
        min_lat = float(self.label_params.get("minimum_latitude", -90.0))
        max_lat = float(self.label_params.get("maximum_latitude", -75.0))
        if lat < min_lat or lat > max_lat:
            raise SiteCoverageError(
                f"Candidate site latitude {lat}° is outside DEM coverage bounds "
                f"[{min_lat}°, {max_lat}°] (north of 75°S)."
            )

    def latlon_to_grid_indices(self, lat: float, lon: float) -> Tuple[float, float, int, int]:
        """
        Validate coverage and convert (lat, lon) to:
        (sample_I_1based, line_J_1based, row_0based, col_0based)
        """
        self.validate_coverage(lat)
        sample_i, line_j = self.processor.latlon_to_pixel(lat, lon)
        row = int(round(line_j - 1))
        col = int(round(sample_i - 1))
        return sample_i, line_j, row, col

    def get_site_elevation(self, lat: float, lon: float) -> float:
        """
        Compute site elevation in metres relative to lunar reference sphere
        using bilinear interpolation from the gridded LOLA DEM.
        Validates coverage [-90, -75] deg.
        """
        self.validate_coverage(lat)
        sample_i, line_j = self.processor.latlon_to_pixel(lat, lon)
        elev = self.get_elevation_array()

        r = line_j - 1.0
        c = sample_i - 1.0
        H, W = elev.shape

        r0 = int(math.floor(r))
        c0 = int(math.floor(c))
        r1 = min(H - 1, r0 + 1)
        c1 = min(W - 1, c0 + 1)
        r0 = max(0, min(H - 1, r0))
        c0 = max(0, min(W - 1, c0))

        dr = r - r0
        dc = c - c0

        val = (
            (1.0 - dr) * (1.0 - dc) * float(elev[r0, c0])
            + dr * (1.0 - dc) * float(elev[r1, c0])
            + (1.0 - dr) * dc * float(elev[r0, c1])
            + dr * dc * float(elev[r1, c1])
        )
        return float(val)


_dem_service_singleton: Optional[DEMService] = None


def get_dem_service() -> DEMService:
    global _dem_service_singleton
    if _dem_service_singleton is None:
        _dem_service_singleton = DEMService()
    return _dem_service_singleton
