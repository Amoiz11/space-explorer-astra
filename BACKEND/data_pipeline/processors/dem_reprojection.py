"""
DEM reprojection module for LOLA lunar south-polar DEMs.

The LOLA south polar DEM (LDEM_75S_240M) is already in its native projection
(Polar Stereographic, MOON_ME_DE421, planetocentric, east-positive longitude,
sphere radius 1737.4 km) as stated in the PDS3 label and DSMAP_POLAR.CAT.

No coordinate reprojection is performed:
  - The label defines a spherical (not ellipsoidal) geometry; no ellipsoid
    flattening correction is needed.
  - The projection is documented and self-consistent.
  - Applying any other projection would require a target CRS that is not
    specified in the SRS for this phase.

What this module does:
  - Provides a function to crop a rectangular lat/lon bounding box from the
    array (in native pixel space, via the LunarCoordinateProcessor).
  - Records conversion metadata for provenance.

If a future phase requires projection conversion (e.g., to equirectangular
for a specific coverage area), that should be implemented here with the
source CRS parameters taken from the label.
"""

import datetime
from typing import Dict, Any, Optional, Tuple
import numpy as np

from data_pipeline.processors.lunar_coordinate_processor import (
    LunarCoordinateProcessor,
)


CONVERSION_METADATA = {
    "reprojection_applied": False,
    "reason": (
        "The LOLA south polar DEM is already in its native documented projection "
        "(Polar Stereographic, sphere radius 1737.4 km, MOON_ME_DE421). "
        "No reprojection is needed or applied. "
        "If a target projection is specified in a future phase, implement it here."
    ),
    "source_projection": "POLAR STEREOGRAPHIC (south, sphere radius 1737.4 km, MOON_ME_DE421)",
    "source_datum": "Sphere, A_AXIS_RADIUS = 1737.4 km (from PDS3 label)",
    "source_coordinate_system": "MOON_ME_DE421 (MEAN EARTH/POLAR AXIS OF DE421)",
    "source_latitude_type": "PLANETOCENTRIC",
    "source_longitude_direction": "EAST (east-positive)",
    "source": "DSMAP_POLAR.CAT, NASA PDS Geosciences Node (fetched)",
    "timestamp": None,  # filled at runtime
}


def get_conversion_metadata() -> Dict[str, Any]:
    """Return a copy of the conversion metadata with current timestamp."""
    meta = dict(CONVERSION_METADATA)
    meta["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return meta


def crop_to_latlon_box(
    elevation_array: np.ndarray,
    processor: LunarCoordinateProcessor,
    south: float,
    north: float,
    west_lon: float,
    east_lon: float,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Crop the elevation array to a lat/lon bounding box by mapping the
    four corners to pixel space and extracting the enclosing rectangle.

    This is an APPROXIMATION suitable for near-polar regions: for the
    south polar stereographic grid, constant-latitude lines are circles,
    not straight rows. The returned rectangle encloses the requested box
    but may include pixels slightly outside it.

    Returns:
        (cropped_array, metadata_dict)
    """
    corners_latlon = [
        (south, west_lon),
        (south, east_lon),
        (north, west_lon),
        (north, east_lon),
    ]
    Is, Js = [], []
    for lat, lon in corners_latlon:
        I, J = processor.latlon_to_pixel(lat, lon)
        Is.append(I)
        Js.append(J)

    col_min = max(0, int(min(Is)) - 1)
    col_max = min(elevation_array.shape[1] - 1, int(max(Is)) + 1)
    row_min = max(0, int(min(Js)) - 1)
    row_max = min(elevation_array.shape[0] - 1, int(max(Js)) + 1)

    cropped = elevation_array[row_min : row_max + 1, col_min : col_max + 1]
    meta = get_conversion_metadata()
    meta["crop"] = {
        "south": south,
        "north": north,
        "west_lon": west_lon,
        "east_lon": east_lon,
        "row_min": row_min,
        "row_max": row_max,
        "col_min": col_min,
        "col_max": col_max,
        "cropped_shape": list(cropped.shape),
    }
    return cropped, meta
