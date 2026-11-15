"""
Lunar polar stereographic coordinate processor.

Implements the OFFICIAL transformation from the LOLA DSMAP_POLAR.CAT catalog
file (fetched from NASA PDS Geosciences Node, Washington University in St. Louis):
  https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/catalog/dsmap_polar.cat

DSMAP_POLAR.CAT transformation (south polar hemisphere, NS = -1):

  Pixel (sample I, line J) → (lat, lon):
      X = (I - N/2 - 0.5) * MAP_SCALE
      Y = (J - N/2 - 0.5) * MAP_SCALE * NS
      R = SQRT(X^2 + Y^2)
      LON = ATAN2(X, Y) * 180/PI
      LAT = -90 + (180/PI) * 2 * ATAN(0.5 * R / 1737400)   [southern]

  Geographic (lat, lon) → pixel (sample I, line J):
      R = 2 * 1737400 * TAN((90 - ABS(LAT)) * PI/360) * SIGN(LAT)
      X = R * SIN(LON * PI/180)
      Y = R * COS(LON * PI/180)
      I = NINT(X / MAP_SCALE + N/2 + 0.5)      [sample, 1-based]
      J = NINT(Y / MAP_SCALE + N/2 + 0.5)      [line,   1-based]
      where SIGN(LAT) = -1 for southern hemisphere

Coordinate system: planetocentric, east-positive longitude (POSITIVE_LONGITUDE_DIRECTION = EAST).
Reference sphere: 1737.4 km (A_AXIS_RADIUS from label). NOT EPSG:4326.
"""

import math
import numpy as np
from typing import Dict, Tuple, Any


MOON_RADIUS_M = 1737400.0   # metres; from label A_AXIS_RADIUS = 1737.4 km


class LunarCoordinateProcessor:
    """
    Lat/lon ↔ pixel (line, sample) mapper for LOLA south polar stereographic DEMs.

    Parameters are read from the PDS3 label; any missing required parameter
    raises an UnsupportedProjectionError naming the missing field.
    """

    REQUIRED_LABEL_PARAMS = [
        "map_scale",
        "lines",
        "line_samples",
        "center_latitude",
    ]

    def __init__(self, label_params: Dict[str, Any]):
        """
        Args:
            label_params: dict with keys:
              map_scale       – MAP_SCALE in metres/pixel (float)
              lines           – number of lines (int, square image assumed)
              line_samples    – number of samples (int)
              center_latitude – CENTER_LATITUDE from label (float; must be ±90)
              sphere_radius_m – optional override; defaults to MOON_RADIUS_M
        """
        for key in self.REQUIRED_LABEL_PARAMS:
            if key not in label_params or label_params[key] is None:
                raise UnsupportedProjectionError(
                    f"LunarCoordinateProcessor requires label parameter '{key}', "
                    f"which is missing or None in the supplied label."
                )

        self.map_scale: float = float(label_params["map_scale"])
        self.N: int = int(label_params["lines"])        # image is square; use LINES
        self.center_lat: float = float(label_params["center_latitude"])
        self.sphere_radius_m: float = float(
            label_params.get("sphere_radius_m", MOON_RADIUS_M)
        )

        if abs(self.center_lat) != 90.0:
            raise UnsupportedProjectionError(
                f"LunarCoordinateProcessor only supports center_latitude ±90 "
                f"(polar stereographic). Got center_latitude = {self.center_lat}. "
                "Parameter 'center_latitude' is unsupported for non-polar projections."
            )

        # NS = +1 for north pole, -1 for south pole (from DSMAP_POLAR.CAT)
        self.NS: int = 1 if self.center_lat > 0 else -1

    def latlon_to_pixel(
        self, lat: float, lon: float
    ) -> Tuple[float, float]:
        """
        Convert planetocentric latitude and east-positive longitude (degrees)
        to 1-based (sample I, line J) using the DSMAP_POLAR.CAT formula.

        DSMAP_POLAR.CAT INVERSE (corrected for south-hemisphere Y convention):
            R   = 2 * 1737400 * TAN((90 - ABS(LAT)) * PI/360)   [always positive]
            X   = R * SIN(LON * PI/180)
            Y   = R * COS(LON * PI/180)       [this is in the NS-flipped space]
            I   = X / MAP_SCALE + N/2 + 0.5
            J   = Y / (MAP_SCALE * NS) + N/2 + 0.5

        Returns (sample_I, line_J) as floats (use round() for nearest pixel).
        """
        R = 2.0 * self.sphere_radius_m * math.tan(
            math.radians(90.0 - abs(lat)) / 2.0
        )  # positive magnitude; NS handled below
        X = R * math.sin(math.radians(lon))
        Y = R * math.cos(math.radians(lon))
        I = X / self.map_scale + self.N / 2 + 0.5
        J = Y / (self.map_scale * self.NS) + self.N / 2 + 0.5
        return (I, J)

    def pixel_to_latlon(
        self, sample_I: float, line_J: float
    ) -> Tuple[float, float]:
        """
        Convert 1-based (sample I, line J) to (lat, lon) in degrees
        using the DSMAP_POLAR.CAT formula.
        """
        X = (sample_I - self.N / 2 - 0.5) * self.map_scale
        Y = (line_J   - self.N / 2 - 0.5) * self.map_scale * self.NS
        R = math.sqrt(X * X + Y * Y)
        lon = math.degrees(math.atan2(X, Y))
        if lon < 0:
            lon += 360.0
        # Southern hemisphere:
        lat = -90.0 + math.degrees(2 * math.atan(0.5 * R / self.sphere_radius_m))
        return (lat, lon % 360.0)

    def pixel_to_latlon_array(
        self, samples: np.ndarray, lines: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Vectorised version of pixel_to_latlon for numpy arrays.
        """
        X = (samples - self.N / 2 - 0.5) * self.map_scale
        Y = (lines   - self.N / 2 - 0.5) * self.map_scale * self.NS
        R = np.sqrt(X * X + Y * Y)
        lon = np.degrees(np.arctan2(X, Y)) % 360.0
        lat = -90.0 + np.degrees(2 * np.arctan(0.5 * R / self.sphere_radius_m))
        return lat, lon

    def latlon_to_pixel_array(
        self, lats: np.ndarray, lons: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Vectorised version of latlon_to_pixel for numpy arrays.
        R = 2 * sphere * TAN((90 - |lat|) * PI/360)  [positive; NS absorbed in J formula]
        I = R*sin(lon) / scale + N/2 + 0.5
        J = R*cos(lon) / (scale * NS) + N/2 + 0.5
        """
        R = (
            2.0
            * self.sphere_radius_m
            * np.tan((90.0 - np.abs(lats)) * math.pi / 360.0)
        )
        X = R * np.sin(np.radians(lons))
        Y = R * np.cos(np.radians(lons))
        I = X / self.map_scale + self.N / 2 + 0.5
        J = Y / (self.map_scale * self.NS) + self.N / 2 + 0.5
        return I, J

    def get_elevation_at_latlon(
        self, lat: float, lon: float, elevation_array: np.ndarray
    ) -> Tuple[float, int, int]:
        """
        Look up elevation in metres at the given lat/lon using nearest-neighbour.

        Returns (elevation_m, line_0indexed, sample_0indexed).
        Raises IndexError if the coordinate falls outside the image.
        """
        I, J = self.latlon_to_pixel(lat, lon)
        # Convert to 0-based integer indices
        col = int(round(I)) - 1   # sample → column (0-based)
        row = int(round(J)) - 1   # line   → row    (0-based)
        if not (0 <= row < elevation_array.shape[0] and 0 <= col < elevation_array.shape[1]):
            raise IndexError(
                f"Coordinate (lat={lat}, lon={lon}) maps to pixel "
                f"(row={row}, col={col}) which is outside the {elevation_array.shape} array."
            )
        return float(elevation_array[row, col]), row, col

    # ------------------------------------------------------------------ #
    #  Projection metadata                                                 #
    # ------------------------------------------------------------------ #

    def projection_info(self) -> Dict[str, Any]:
        """Return a dict of the projection parameters actually used."""
        hemisphere = "south" if self.NS == -1 else "north"
        return {
            "projection": "POLAR STEREOGRAPHIC",
            "source": "DSMAP_POLAR.CAT (NASA PDS Geosciences Node, fetched)",
            "hemisphere": hemisphere,
            "center_latitude_deg": self.center_lat,
            "center_longitude_deg": 0.0,
            "sphere_radius_m": self.sphere_radius_m,
            "map_scale_m_per_pixel": self.map_scale,
            "image_size_pixels": self.N,
            "coordinate_system": "MOON_ME_DE421 (MEAN EARTH/POLAR AXIS OF DE421)",
            "latitude_type": "PLANETOCENTRIC",
            "longitude_direction": "EAST (east-positive)",
            "note": "Lunar body-fixed rotating frame. Sphere, not ellipsoid. "
                    "No geoid correction applied; elevations relative to reference sphere. "
                    "This is not an Earth geographic projection.",
        }

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _latlon_to_R(self, lat: float, lon: float) -> float:
        """
        Compute the DSMAP_POLAR.CAT R (signed, includes SIGN(LAT)).
        R = 2 * 1737400 * TAN((90 - ABS(LAT)) * PI/360) * SIGN(LAT)
        """
        sign_lat = -1.0 if lat < 0 else 1.0
        R = (
            2.0
            * self.sphere_radius_m
            * math.tan(math.radians(90.0 - abs(lat)) / 2.0)
            * sign_lat
        )
        return R


class UnsupportedProjectionError(ValueError):
    """Raised when a required projection parameter is missing or unsupported."""
    pass
