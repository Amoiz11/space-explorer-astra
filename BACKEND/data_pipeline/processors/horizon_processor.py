"""
Horizon profile processor for lunar terrain using gridded DEMs.

Implements:
  - Ray-marching along azimuths (default step 1.0 deg, clockwise from North).
  - Step size of 1 DEM pixel (240 m).
  - Bilinear elevation interpolation of the DEM array.
  - Spherical Moon curvature drop: delta_z = d^2 / (2 * R_moon).
  - Observer height = site DEM elevation + optional observer_height_m (default 0).
  - Coverage-edge termination at 75°S boundary or grid borders, tracking cut azimuths.
  - Maximum elevation angle per ray defines the local terrain horizon elevation and blocking distance.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


MOON_RADIUS_M = 1737400.0   # metres; from label A_AXIS_RADIUS = 1737.4 km
MAP_SCALE_M = 240.0         # metres/pixel; from label MAP_SCALE


class HorizonProcessor:
    """
    Computes topocentric horizon elevation profiles from gridded polar DEMs.
    """

    METHOD_NAME = "Bilinear ray-marching with spherical curvature drop (Horn/LOLA)"
    DISCLAIMERS = [
        "A 240 m DEM baseline cannot represent ridges, boulders, or micro-terrain smaller than its resolution, "
        "so the real horizon can be higher or lower.",
        "Planning support tool, not safety certification.",
        "Spherical curvature drop uses Moon mean radius 1737.4 km from PDS label.",
    ]

    def __init__(
        self,
        moon_radius_m: float = MOON_RADIUS_M,
        map_scale_m: float = MAP_SCALE_M,
    ):
        self.moon_radius_m = float(moon_radius_m)
        self.map_scale_m = float(map_scale_m)

    def bilinear_sample_point(self, elev: np.ndarray, r: float, c: float) -> float:
        """Bilinearly sample elevation at a single fractional pixel (r, c)."""
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
            (1.0 - dr) * (1.0 - dc) * elev[r0, c0]
            + dr * (1.0 - dc) * elev[r1, c0]
            + (1.0 - dr) * dc * elev[r0, c1]
            + dr * dc * elev[r1, c1]
        )
        return float(val)

    def compute_horizon_profile(
        self,
        elev_array: np.ndarray,
        site_row: float,
        site_col: float,
        site_lon_deg: float,
        site_lat_deg: float,
        azimuth_step_deg: float = 1.0,
        max_distance_km: float = 100.0,
        observer_height_m: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Compute the 360-degree horizon profile for an observer at (site_row, site_col).

        Args:
            elev_array: 2D numpy array of elevations in metres.
            site_row: 0-based row coordinate of the site.
            site_col: 0-based col coordinate of the site.
            site_lon_deg: planetocentric longitude in degrees (east-positive).
            site_lat_deg: planetocentric latitude in degrees.
            azimuth_step_deg: azimuth resolution in degrees (default 1.0).
            max_distance_km: maximum search radius in km (default 100.0).
            observer_height_m: additional instrument/mast height in metres (default 0.0).

        Returns:
            Dictionary containing profile series, summary metrics, cut azimuth count, etc.
        """
        H, W = elev_array.shape
        r_center = (H - 1) / 2.0
        c_center = (W - 1) / 2.0

        # Elevation at observer position from DEM
        z_dem_site = self.bilinear_sample_point(elev_array, site_row, site_col)
        z0 = z_dem_site + float(observer_height_m)

        # Azimuth array [0, 360)
        if azimuth_step_deg <= 0.0 or azimuth_step_deg > 45.0:
            raise ValueError(f"Invalid azimuth_step_deg: {azimuth_step_deg}. Must be between 0.01 and 45.0.")
        if max_distance_km <= 0.0 or max_distance_km > 500.0:
            raise ValueError(f"Invalid max_distance_km: {max_distance_km}. Must be between 0.1 and 500.0.")

        azimuths = np.arange(0.0, 360.0, float(azimuth_step_deg))

        # Steps along rays (step size = map_scale_m = 240 m)
        max_steps = int(math.ceil(max_distance_km * 1000.0 / self.map_scale_m))
        if max_steps < 1:
            max_steps = 1
        steps = np.arange(1, max_steps + 1, dtype=np.float64)
        distances_m = steps * self.map_scale_m

        # Polar stereographic ray angle: in DSMAP_POLAR.CAT, azimuth from North
        # at meridian lon0 satisfies:
        # u_X = sin(lon0 + az)
        # u_Y = cos(lon0 + az)
        # delta_col = +s * sin(lon0 + az)
        # delta_row = -s * cos(lon0 + az)
        ray_angles = np.radians(float(site_lon_deg) + azimuths)

        # Coordinates for all (azimuths, steps) -> shape: (N_az, N_steps)
        r_coords = site_row - steps[None, :] * np.cos(ray_angles[:, None])
        c_coords = site_col + steps[None, :] * np.sin(ray_angles[:, None])

        r_min_idx = np.floor(r_coords).astype(int)
        c_min_idx = np.floor(c_coords).astype(int)
        r_max_idx = r_min_idx + 1
        c_max_idx = c_min_idx + 1

        # 75°S boundary radius in pixels
        # Distance from pole R = 2 * R_moon * tan((90 - 75)/2 deg) = 2 * R_moon * tan(7.5 deg)
        R_75_pix = (2.0 * self.moon_radius_m * math.tan(math.radians(7.5))) / self.map_scale_m
        dist_from_pole_pix = np.sqrt((r_coords - r_center) ** 2 + (c_coords - c_center) ** 2)

        # Validity mask: inside image bounds and south of -75°S
        is_valid_point = (
            (r_min_idx >= 0)
            & (r_max_idx < H)
            & (c_min_idx >= 0)
            & (c_max_idx < W)
            & (dist_from_pole_pix <= R_75_pix)
        )

        # Ray stops at first invalid point
        cum_valid = np.cumprod(is_valid_point, axis=1, dtype=bool)

        # Bilinear interpolation for valid points
        dr = r_coords - r_min_idx
        dc = c_coords - c_min_idx

        z = np.zeros_like(r_coords, dtype=np.float64)
        v = cum_valid

        # Extract values
        z[v] = (
            (1.0 - dr[v]) * (1.0 - dc[v]) * elev_array[r_min_idx[v], c_min_idx[v]]
            + dr[v] * (1.0 - dc[v]) * elev_array[r_max_idx[v], c_min_idx[v]]
            + (1.0 - dr[v]) * dc[v] * elev_array[r_min_idx[v], c_max_idx[v]]
            + dr[v] * dc[v] * elev_array[r_max_idx[v], c_max_idx[v]]
        )

        # Spherical curvature drop: delta_z = d^2 / (2 * R_moon)
        curv_drop = (distances_m[None, :] ** 2) / (2.0 * self.moon_radius_m)

        # Elevation angle (radians): atan((z - curv_drop - z0) / d)
        elev_diff = z - curv_drop - z0
        theta_deg = np.degrees(np.arctan(elev_diff / distances_m[None, :]))

        # Points outside validity set to strongly negative
        theta_deg[~cum_valid] = -999.0

        # Maximum elevation angle along each ray
        horizon_elevations = np.max(theta_deg, axis=1)
        max_step_indices = np.argmax(theta_deg, axis=1)
        blocking_distances_km = distances_m[max_step_indices] / 1000.0

        # Check if ray was cut short by coverage edge
        # (i.e. not all steps were valid)
        cut_by_coverage = ~cum_valid[:, -1]
        cut_azimuths = [float(azimuths[i]) for i in range(len(azimuths)) if cut_by_coverage[i]]

        # Profile list
        profile = []
        for i in range(len(azimuths)):
            profile.append({
                "azimuth_deg": round(float(azimuths[i]), 2),
                "horizon_elevation_deg": round(float(horizon_elevations[i]), 4),
                "distance_to_blocking_pixel_km": round(float(blocking_distances_km[i]), 3),
                "cut_by_coverage": bool(cut_by_coverage[i]),
            })

        max_idx = int(np.argmax(horizon_elevations))
        min_idx = int(np.argmin(horizon_elevations))

        summary = {
            "min_horizon_elevation_deg": round(float(horizon_elevations[min_idx]), 4),
            "max_horizon_elevation_deg": round(float(horizon_elevations[max_idx]), 4),
            "mean_horizon_elevation_deg": round(float(np.mean(horizon_elevations)), 4),
            "max_horizon_azimuth_deg": round(float(azimuths[max_idx]), 2),
            "cut_azimuth_count": int(len(cut_azimuths)),
        }

        return {
            "method": self.METHOD_NAME,
            "observer_height_dem_m": round(z_dem_site, 2),
            "observer_height_m": float(observer_height_m),
            "total_observer_height_m": round(z0, 2),
            "max_distance_km": float(max_distance_km),
            "azimuth_step_deg": float(azimuth_step_deg),
            "summary": summary,
            "cut_azimuths": cut_azimuths,
            "profile": profile,
            "disclaimers": self.DISCLAIMERS,
        }
