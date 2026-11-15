"""
Slope and terrain morphology processor for gridded DEMs.

Implements:
  - Horn (1981) 8-neighbor weighted finite-difference gradient for slope calculation (degrees).
  - Scale distortion documentation: Polar stereographic projection has true scale at -90°S;
    scale distortion reaches ~1.73% at -75°S boundary (documented, ignored for slope estimation).
  - Baseline limitation: 240 m baseline cannot represent slopes or micro-hazards at smaller scales.
  - Analysis area extraction: circular radius or landing ellipse (semi_major_m, semi_minor_m, orientation_deg).
  - Morphologic metrics: mean, max, percentiles (50, 90, 95), histogram of slope, elevation min/max/mean,
    local relief (max - min elevation), and roughness (RMS elevation deviation).
  - User-adjustable criteria evaluation (fraction exceeding threshold, explicitly labeled as example threshold).
"""

import math
import numpy as np
from typing import Dict, Any, Tuple, Optional, List


class SlopeProcessor:
    """
    Computes slope and terrain roughness metrics from a 2D elevation grid.
    """

    METHOD_NAME = "Horn (1981) 8-neighbor finite difference"
    ROUGHNESS_METHOD = "RMS elevation deviation (standard deviation) and peak-to-peak local relief"
    SCALE_DISTORTION_NOTE = (
        "Polar stereographic scale factor k = 2 / (1 + sin(|lat|)). At -90°S k=1.000; "
        "at the -75°S boundary k=1.0173 (approx 1.73% scale expansion). The distortion is "
        "documented and not corrected; estimated slope error due to distortion is < 2% at boundary."
    )
    BASELINE_DISCLAIMER = (
        "A 240 m DEM baseline cannot detect or represent slopes, boulders, or micro-hazards "
        "at scales smaller than 240 m. Terrain cannot be certified as safe for landing."
    )

    def __init__(self, pixel_spacing_m: float = 240.0):
        self.pixel_spacing_m = float(pixel_spacing_m)

    def compute_slope_grid(self, elev: np.ndarray) -> np.ndarray:
        """
        Compute slope in degrees for each cell of a 2D float32/float64 elevation array
        using Horn's (1981) 8-neighbor weighted gradient formula:

            dz/dx = ((z[i-1,j+1] + 2*z[i,j+1] + z[i+1,j+1]) - (z[i-1,j-1] + 2*z[i,j-1] + z[i+1,j-1])) / (8 * dx)
            dz/dy = ((z[i+1,j-1] + 2*z[i+1,j] + z[i+1,j+1]) - (z[i-1,j-1] + 2*z[i-1,j] + z[i-1,j+1])) / (8 * dy)
            slope = arctan(sqrt((dz/dx)^2 + (dz/dy)^2)) * 180 / pi

        Border pixels are padded with edge replication so slope has the same shape as elev.
        """
        if elev.ndim != 2:
            raise ValueError(f"Expected 2D elevation array, got ndim={elev.ndim}")

        # Pad with edge values for border handling
        padded = np.pad(elev, pad_width=1, mode='edge').astype(np.float64)

        # 8 neighbors
        z_nw = padded[:-2, :-2]
        z_n  = padded[:-2, 1:-1]
        z_ne = padded[:-2, 2:]
        z_w  = padded[1:-1, :-2]
        z_e  = padded[1:-1, 2:]
        z_sw = padded[2:, :-2]
        z_s  = padded[2:, 1:-1]
        z_se = padded[2:, 2:]

        dx = self.pixel_spacing_m
        dy = self.pixel_spacing_m

        # Horn gradient
        dz_dx = ((z_ne + 2.0 * z_e + z_se) - (z_nw + 2.0 * z_w + z_sw)) / (8.0 * dx)
        dz_dy = ((z_sw + 2.0 * z_s + z_se) - (z_nw + 2.0 * z_n + z_ne)) / (8.0 * dy)

        grad = np.sqrt(dz_dx ** 2 + dz_dy ** 2)
        slope_deg = np.degrees(np.arctan(grad)).astype(np.float32)
        return slope_deg

    def get_ellipse_mask(
        self,
        grid_shape: Tuple[int, int],
        center_row: float,
        center_col: float,
        semi_major_m: Optional[float] = None,
        semi_minor_m: Optional[float] = None,
        orientation_deg: Optional[float] = None,
        analysis_radius_m: float = 1000.0,
    ) -> np.ndarray:
        """
        Create a boolean mask (same shape as grid) for pixels inside the landing area.
        If semi_major_m and semi_minor_m are provided, computes an elliptical footprint.
        Otherwise, uses circular radius analysis_radius_m.
        """
        rows, cols = grid_shape
        # Use a bounding box around center to optimize
        max_dim_m = max(semi_major_m or analysis_radius_m, semi_minor_m or analysis_radius_m, analysis_radius_m)
        r_pix = int(math.ceil(max_dim_m / self.pixel_spacing_m)) + 2

        r_min = max(0, int(math.floor(center_row - r_pix)))
        r_max = min(rows, int(math.ceil(center_row + r_pix + 1)))
        c_min = max(0, int(math.floor(center_col - r_pix)))
        c_max = min(cols, int(math.ceil(center_col + r_pix + 1)))

        mask = np.zeros((rows, cols), dtype=bool)
        if r_min >= r_max or c_min >= c_max:
            return mask

        sub_r, sub_c = np.ogrid[r_min:r_max, c_min:c_max]
        # Distances in metres
        # In grid: dy = (row - center_row) * spacing, dx = (col - center_col) * spacing
        dy = (sub_r - center_row) * self.pixel_spacing_m
        dx = (sub_c - center_col) * self.pixel_spacing_m

        if semi_major_m is not None and semi_minor_m is not None and semi_major_m > 0 and semi_minor_m > 0:
            a = float(semi_major_m)
            b = float(semi_minor_m)
            theta = math.radians(float(orientation_deg or 0.0))
            # Rotate coordinates
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            # x' = dx * cos - dy * sin
            # y' = dx * sin + dy * cos
            x_rot = dx * cos_t - dy * sin_t
            y_rot = dx * sin_t + dy * cos_t
            inside = ((x_rot / a) ** 2 + (y_rot / b) ** 2) <= 1.0
        else:
            radius = float(analysis_radius_m)
            inside = (dx ** 2 + dy ** 2) <= (radius ** 2)

        mask[r_min:r_max, c_min:c_max] = inside
        # Ensure at least the center pixel is included if area is very small
        cr_idx = int(round(center_row))
        cc_idx = int(round(center_col))
        if 0 <= cr_idx < rows and 0 <= cc_idx < cols:
            mask[cr_idx, cc_idx] = True
        return mask

    def compute_terrain_statistics(
        self,
        elev_grid: np.ndarray,
        slope_grid: np.ndarray,
        mask: np.ndarray,
        criteria: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compute morphologic and slope statistics for pixels where mask == True.
        """
        elev_pts = elev_grid[mask]
        slope_pts = slope_grid[mask]

        if len(elev_pts) == 0:
            raise ValueError("No pixels found inside the landing analysis footprint.")

        # Elevation stats
        min_elev = float(np.min(elev_pts))
        max_elev = float(np.max(elev_pts))
        mean_elev = float(np.mean(elev_pts))
        local_relief = float(max_elev - min_elev)
        roughness_rms = float(np.std(elev_pts))

        # Slope stats
        min_slope = float(np.min(slope_pts))
        max_slope = float(np.max(slope_pts))
        mean_slope = float(np.mean(slope_pts))
        p50_slope = float(np.percentile(slope_pts, 50))
        p90_slope = float(np.percentile(slope_pts, 90))
        p95_slope = float(np.percentile(slope_pts, 95))

        # Slope histogram: 10 bins between 0 and max(30, ceil(max_slope))
        hist_max = max(30.0, float(math.ceil(max_slope)))
        counts, bin_edges = np.histogram(slope_pts, bins=10, range=(0.0, hist_max))
        histogram = {
            "counts": [int(c) for c in counts],
            "bin_edges_deg": [float(round(b, 2)) for b in bin_edges],
            "total_pixels": int(len(slope_pts)),
        }

        # Criteria evaluation (default threshold 15.0 degrees if not specified)
        criteria_cfg = criteria or {}
        slope_threshold = float(criteria_cfg.get("slope_threshold_deg", 15.0))
        exceeding_pixels = int(np.sum(slope_pts > slope_threshold))
        fraction_exceeding = float(exceeding_pixels / len(slope_pts))

        criteria_result = {
            "slope_threshold_deg": slope_threshold,
            "threshold_label": "example threshold, not an official safety criterion",
            "exceeding_pixel_count": exceeding_pixels,
            "total_pixel_count": int(len(slope_pts)),
            "fraction_exceeding_threshold": round(fraction_exceeding, 4),
            "percentage_exceeding_threshold": round(fraction_exceeding * 100.0, 2),
            "site_safety_disclaimer": "Site is never labelled safe. Threshold is an illustrative user parameter.",
        }

        return {
            "pixel_count": int(len(slope_pts)),
            "elevation": {
                "min_m": round(min_elev, 2),
                "max_m": round(max_elev, 2),
                "mean_m": round(mean_elev, 2),
                "local_relief_m": round(local_relief, 2),
                "roughness_rms_m": round(roughness_rms, 2),
                "roughness_method": self.ROUGHNESS_METHOD,
                "vertical_reference": "reference sphere (radius 1737.4 km)",
            },
            "slope": {
                "mean_deg": round(mean_slope, 2),
                "max_deg": round(max_slope, 2),
                "min_deg": round(min_slope, 2),
                "p50_deg": round(p50_slope, 2),
                "p90_deg": round(p90_slope, 2),
                "p95_deg": round(p95_slope, 2),
                "method": self.METHOD_NAME,
                "pixel_spacing_m": self.pixel_spacing_m,
                "histogram": histogram,
            },
            "scale_distortion_note": self.SCALE_DISTORTION_NOTE,
            "disclaimer": self.BASELINE_DISCLAIMER,
            "criteria_result": criteria_result,
        }
