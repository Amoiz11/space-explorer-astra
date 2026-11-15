"""
Earth visibility processor for lunar landing sites (LL-19 to LL-22).

Implements:
- Direct-to-Earth line-of-sight visibility against local terrain horizon.
- Criteria options: earth_disk="center" (default) or "upper_limb" (Earth radius 6378.1366 km).
- Obstruction status per step:
  - "clear": Earth elevation is above the local terrain horizon.
  - "blocked_by_terrain": Earth elevation > 0 deg but below terrain horizon.
  - "below_horizon": Earth elevation <= 0 deg and below terrain horizon.
- Contiguous visibility windows with linear interpolation boundary refinement.
- Mean azimuth and elevation per window.
- Explicit non-modelled relay communication statement (LL-21).
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from data_pipeline.processors.illumination_processor import (
    parse_iso_timestamp,
    format_iso_timestamp,
    refine_continuous_windows,
)

# Earth equatorial radius from NAIF generic PCK pck00010.tpc (bodvrd('EARTH', 'RADII', 3))
EARTH_EQUATORIAL_RADIUS_KM = 6378.1366


def compute_earth_angular_radius_deg(
    distance_km: float,
    earth_radius_km: float = EARTH_EQUATORIAL_RADIUS_KM,
) -> float:
    """Compute topocentric angular radius of the Earth in degrees."""
    if distance_km <= earth_radius_km:
        return 90.0
    return math.degrees(math.asin(earth_radius_km / distance_km))


def determine_obstruction_status(
    effective_elevation_deg: float,
    horizon_elevation_deg: float,
) -> str:
    """
    Classify obstruction status:
    - "clear": elevation above terrain horizon.
    - "blocked_by_terrain": elevation > 0 deg but <= terrain horizon.
    - "below_horizon": elevation <= 0 deg and <= terrain horizon.
    """
    if effective_elevation_deg > horizon_elevation_deg:
        return "clear"
    elif effective_elevation_deg > 0.0:
        return "blocked_by_terrain"
    else:
        return "below_horizon"


def circular_mean_degrees(angles_deg: List[float]) -> float:
    """Compute circular mean of angles in degrees [0, 360)."""
    if not angles_deg:
        return 0.0
    rads = np.radians(angles_deg)
    sin_sum = np.sum(np.sin(rads))
    cos_sum = np.sum(np.cos(rads))
    mean_rad = np.arctan2(sin_sum, cos_sum)
    mean_deg = np.degrees(mean_rad) % 360.0
    return float(mean_deg)


class EarthVisibilityProcessor:
    """
    Computes Earth line-of-sight visibility against local terrain horizons.
    """

    METHOD_NAME = "SPICE geometric with terrain horizon from a 240 m DEM"
    RELAY_NOTE = "Direct-to-Earth line-of-sight only. Relay satellites or orbital nodes are not modelled (LL-21)."
    DISCLAIMERS = [
        "Geometric visibility is not a guaranteed radio link.",
        "A 240 m DEM cannot represent terrain smaller than its resolution so real shadows can differ.",
        "Planning support tool, not safety certification.",
        "Direct-to-Earth line-of-sight only. Relay satellites are not modelled.",
    ]

    def __init__(self, earth_radius_km: float = EARTH_EQUATORIAL_RADIUS_KM):
        self.earth_radius_km = float(earth_radius_km)

    def process_visibility_series(
        self,
        ephemeris_series: List[Dict[str, Any]],
        horizon_profile: List[Dict[str, Any]],
        horizon_interp_func,
        earth_disk: str = "center",
    ) -> Dict[str, Any]:
        """
        Process ephemeris steps into Earth visibility timeline, windows, and totals.

        Args:
            ephemeris_series: list of dicts with keys:
                - timestamp: str
                - earth_azimuth_deg: float
                - earth_elevation_deg: float
                - earth_distance_km: float (optional, default ~384400 km)
            horizon_profile: list of {"azimuth_deg": ..., "horizon_elevation_deg": ...}
            horizon_interp_func: callable(profile, az_deg) -> float
            earth_disk: "center" (default) or "upper_limb"

        Returns:
            Dictionary with series, windows, totals, method, relay_communication, disclaimers.
        """
        if earth_disk not in ("center", "upper_limb"):
            raise ValueError(f"Invalid earth_disk option: '{earth_disk}'. Must be 'center' or 'upper_limb'.")

        if not ephemeris_series:
            return {
                "series": [],
                "windows": [],
                "totals": {
                    "earth_visible_hours": 0.0,
                    "blocked_by_terrain_hours": 0.0,
                    "below_horizon_hours": 0.0,
                    "total_simulation_hours": 0.0,
                    "earth_visible_fraction": 0.0,
                    "number_of_windows": 0,
                },
                "relay_communication": "not modelled",
                "relay_communication_note": self.RELAY_NOTE,
                "disclaimers": self.DISCLAIMERS,
            }

        timestamps = []
        series_points = []
        visibility_signals = []  # h_eff - h_horiz
        blocked_count = 0
        below_horiz_count = 0
        clear_count = 0

        for step in ephemeris_series:
            ts = step["timestamp"]
            timestamps.append(ts)
            earth_az = float(step.get("earth_azimuth_deg", step.get("earth_azimuth", 0.0)))
            earth_el = float(step.get("earth_elevation_deg", step.get("earth_elevation", 0.0)))
            earth_dist = float(step.get("earth_distance_km", 384400.0))

            ang_radius = compute_earth_angular_radius_deg(earth_dist, self.earth_radius_km)

            if earth_disk == "upper_limb":
                eff_el = earth_el + ang_radius
            else:
                eff_el = earth_el

            h_horiz = horizon_interp_func(horizon_profile, earth_az)
            status = determine_obstruction_status(eff_el, h_horiz)

            if status == "clear":
                clear_count += 1
            elif status == "blocked_by_terrain":
                blocked_count += 1
            else:
                below_horiz_count += 1

            # Signal for window detection: eff_el > h_horiz
            visibility_signals.append(eff_el - h_horiz)

            series_points.append({
                "timestamp": ts,
                "earth_azimuth": round(earth_az, 2),
                "earth_elevation": round(earth_el, 2),
                "earth_azimuth_deg": round(earth_az, 2),
                "earth_elevation_deg": round(earth_el, 2),
                "horizon_elevation_at_earth_azimuth": round(h_horiz, 2),
                "effective_elevation_deg": round(eff_el, 2),
                "earth_angular_radius_deg": round(ang_radius, 4),
                "obstruction_status": status,
                "earth_visible": (status == "clear"),
            })

        # Calculate simulation duration matching ephemeris steps
        total_sim_hours = round(len(ephemeris_series) * (30.0 / 60.0), 2)
        step_sec = 1800.0
        if len(timestamps) >= 2:
            dt_start = parse_iso_timestamp(timestamps[0])
            dt_end = parse_iso_timestamp(timestamps[-1])
            step_sec = (parse_iso_timestamp(timestamps[1]) - dt_start).total_seconds()
            total_sim_hours = round(len(timestamps) * (step_sec / 3600.0), 2)

        # Refine windows via linear interpolation
        windows_raw = refine_continuous_windows(
            timestamps, visibility_signals, threshold=0.0, inclusive_ge=False, step_sec=step_sec
        )

        # For each window, compute mean azimuth and elevation
        dts = [parse_iso_timestamp(ts) for ts in timestamps]
        t0 = dts[0]
        t_secs = [(dt - t0).total_seconds() for dt in dts]

        windows = []
        for w in windows_raw:
            w_start_sec = w["start_sec"]
            w_end_sec = w["end_sec"]

            # Collect points that fall within or span this window
            az_in_w = []
            el_in_w = []
            for i, t_s in enumerate(t_secs):
                if w_start_sec <= t_s <= w_end_sec:
                    az_in_w.append(series_points[i]["earth_azimuth"])
                    el_in_w.append(series_points[i]["earth_elevation"])

            # If no discrete step fell inside the window, sample start and end
            if not az_in_w:
                # Find nearest steps
                for i in range(len(t_secs) - 1):
                    if t_secs[i] <= w_start_sec and t_secs[i + 1] >= w_end_sec:
                        az_in_w = [series_points[i]["earth_azimuth"], series_points[i + 1]["earth_azimuth"]]
                        el_in_w = [series_points[i]["earth_elevation"], series_points[i + 1]["earth_elevation"]]
                        break

            mean_az = circular_mean_degrees(az_in_w) if az_in_w else 0.0
            mean_el = float(np.mean(el_in_w)) if el_in_w else 0.0

            windows.append({
                "start": w["start"],
                "end": w["end"],
                "duration_hours": w["duration_hours"],
                "mean_earth_azimuth": round(mean_az, 2),
                "mean_earth_elevation": round(mean_el, 2),
            })

        # Calculate simulation duration matching ephemeris steps
        total_sim_hours = round(len(ephemeris_series) * (30.0 / 60.0), 2)
        if len(timestamps) >= 2:
            dt_start = parse_iso_timestamp(timestamps[0])
            dt_end = parse_iso_timestamp(timestamps[-1])
            step_sec = (parse_iso_timestamp(timestamps[1]) - dt_start).total_seconds()
            total_sim_hours = round(len(timestamps) * (step_sec / 3600.0), 2)

        earth_visible_hours = round(sum(w["duration_hours"] for w in windows), 4)

        # Proportionally attribute remaining time to blocked vs below-horizon based on discrete steps
        non_clear_steps = blocked_count + below_horiz_count
        non_clear_hours = max(0.0, total_sim_hours - earth_visible_hours)
        if non_clear_steps > 0:
            blocked_hours = round(non_clear_hours * (blocked_count / non_clear_steps), 2)
            below_horiz_hours = round(non_clear_hours * (below_horiz_count / non_clear_steps), 2)
        else:
            blocked_hours = 0.0
            below_horiz_hours = 0.0

        fraction_vis = round(earth_visible_hours / total_sim_hours, 4) if total_sim_hours > 0 else 0.0

        totals = {
            "earth_visible_hours": round(earth_visible_hours, 2),
            "blocked_by_terrain_hours": blocked_hours,
            "below_horizon_hours": below_horiz_hours,
            "total_simulation_hours": round(total_sim_hours, 2),
            "earth_visible_fraction": fraction_vis,
            "number_of_windows": len(windows),
            "boundary_refinement_method": "linear interpolation between time steps",
        }

        return {
            "series": series_points,
            "windows": windows,
            "totals": totals,
            "relay_communication": "not modelled",
            "relay_communication_note": self.RELAY_NOTE,
            "method": self.METHOD_NAME,
            "disclaimers": self.DISCLAIMERS,
        }
