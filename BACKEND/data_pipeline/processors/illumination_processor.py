"""
Illumination processor for lunar landing sites (LL-14 to LL-16).

Implements:
- Solar disk modeling (angular radius from SPICE distance and PCK Sun radius).
- Circular segment geometry for fraction of solar disk above the local terrain horizon.
- Classification into "lit" (fraction = 1), "partial" (0 < fraction < 1), and "shadow" (fraction = 0).
- Contiguous window detection with linear interpolation boundary refinement for
  "any part lit" and "fully lit" conditions.
- Window and shadow duration statistics.
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple


# Sun radius from NAIF generic PCK pck00010.tpc (bodvrd('SUN', 'RADII', 3))
SUN_RADIUS_KM = 696000.0


def compute_solar_angular_radius_deg(distance_km: float, sun_radius_km: float = SUN_RADIUS_KM) -> float:
    """
    Compute the topocentric angular radius of the Sun in degrees.
    theta_rad = arcsin(R_sun / D)
    """
    if distance_km <= sun_radius_km:
        return 90.0
    return math.degrees(math.asin(sun_radius_km / distance_km))


def compute_illuminated_fraction(
    sun_elevation_deg: float,
    horizon_elevation_deg: float,
    angular_radius_deg: float,
) -> Tuple[float, str]:
    """
    Compute fraction of the solar disk above the local terrain horizon using
    circular segment geometry.

    Args:
        sun_elevation_deg: Sun center elevation in degrees.
        horizon_elevation_deg: Local terrain horizon elevation in degrees.
        angular_radius_deg: Sun's angular radius in degrees.

    Returns:
        (illuminated_fraction, status)
        illuminated_fraction in [0.0, 1.0]
        status in ["lit", "partial", "shadow"]
    """
    if angular_radius_deg <= 0.0:
        # Fall back to point source
        if sun_elevation_deg > horizon_elevation_deg:
            return 1.0, "lit"
        return 0.0, "shadow"

    delta_h = sun_elevation_deg - horizon_elevation_deg
    x = delta_h / angular_radius_deg  # normalized elevation of Sun center above horizon

    if x >= 1.0:
        return 1.0, "lit"
    elif x <= -1.0:
        return 0.0, "shadow"
    else:
        # Circular segment area formula:
        # Fraction = 0.5 + (1/pi) * (arcsin(x) + x * sqrt(1 - x^2))
        fraction = 0.5 + (1.0 / math.pi) * (math.asin(x) + x * math.sqrt(max(0.0, 1.0 - x * x)))
        fraction = max(0.0, min(1.0, fraction))
        if fraction >= 1.0:
            return 1.0, "lit"
        elif fraction <= 0.0:
            return 0.0, "shadow"
        return fraction, "partial"


def parse_iso_timestamp(ts: str) -> datetime:
    """Parse ISO UTC timestamp string into timezone-aware datetime."""
    clean = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def format_iso_timestamp(dt: datetime) -> str:
    """Format timezone-aware datetime into UTC ISO string."""
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def refine_continuous_windows(
    timestamps_iso: List[str],
    signal_values: List[float],
    threshold: float = 0.0,
    inclusive_ge: bool = False,
    step_sec: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Find contiguous intervals where signal_values > threshold (or >= if inclusive_ge).
    Refines start and end times via linear interpolation between discrete time steps.

    Returns list of dicts: {"start": ISO, "end": ISO, "duration_hours": float, "start_sec": float, "end_sec": float}
    """
    n = len(timestamps_iso)
    if n == 0 or len(signal_values) != n:
        return []

    dts = [parse_iso_timestamp(ts) for ts in timestamps_iso]
    t0 = dts[0]
    t_secs = [(dt - t0).total_seconds() for dt in dts]

    if step_sec is None:
        step_sec = (t_secs[1] - t_secs[0]) if n >= 2 else 3600.0

    # Evaluate boolean state at each discrete step
    states = [
        (v >= threshold if inclusive_ge else v > threshold)
        for v in signal_values
    ]

    windows: List[Dict[str, Any]] = []
    in_window = False
    cur_start_sec = 0.0

    for i in range(n):
        is_active = states[i]

        if not in_window and is_active:
            # Transition from inactive to active
            in_window = True
            if i == 0:
                cur_start_sec = t_secs[0]
            else:
                # Linear interpolation between i-1 and i
                v_prev = signal_values[i - 1] - threshold
                v_curr = signal_values[i] - threshold
                denom = v_curr - v_prev
                if abs(denom) > 1e-12:
                    frac = (-v_prev) / denom
                    frac = max(0.0, min(1.0, frac))
                else:
                    frac = 0.5
                cur_start_sec = t_secs[i - 1] + frac * (t_secs[i] - t_secs[i - 1])

        elif in_window and not is_active:
            # Transition from active to inactive
            in_window = False
            v_prev = signal_values[i - 1] - threshold
            v_curr = signal_values[i] - threshold
            denom = v_prev - v_curr
            if abs(denom) > 1e-12:
                frac = v_prev / denom
                frac = max(0.0, min(1.0, frac))
            else:
                frac = 0.5
            end_sec = t_secs[i - 1] + frac * (t_secs[i] - t_secs[i - 1])

            duration_h = max(0.0, (end_sec - cur_start_sec) / 3600.0)
            start_dt = datetime.fromtimestamp(t0.timestamp() + cur_start_sec, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(t0.timestamp() + end_sec, tz=timezone.utc)

            windows.append({
                "start": format_iso_timestamp(start_dt),
                "end": format_iso_timestamp(end_dt),
                "duration_hours": round(duration_h, 4),
                "start_sec": cur_start_sec,
                "end_sec": end_sec,
            })

    # If still active at end of simulation, cover the full interval of the final active step
    if in_window:
        end_sec = t_secs[-1] + step_sec
        duration_h = max(0.0, (end_sec - cur_start_sec) / 3600.0)
        start_dt = datetime.fromtimestamp(t0.timestamp() + cur_start_sec, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(t0.timestamp() + end_sec, tz=timezone.utc)
        windows.append({
            "start": format_iso_timestamp(start_dt),
            "end": format_iso_timestamp(end_dt),
            "duration_hours": round(duration_h, 4),
            "start_sec": cur_start_sec,
            "end_sec": end_sec,
        })

    return windows


class IlluminationProcessor:
    """
    Computes solar illumination timeline, disk fractions, lit/partial/shadow states,
    and contiguous visibility windows using terrain horizon profiles.
    """

    METHOD_NAME = "SPICE geometric with terrain horizon from a 240 m DEM"
    DISCLAIMERS = [
        "Geometric visibility is not a guaranteed radio link.",
        "Sunlight is not guaranteed electrical power.",
        "A 240 m DEM cannot represent terrain smaller than its resolution so real shadows can differ.",
        "Planning support tool, not safety certification.",
        "Low-angle sunlight near the horizon is not the same as usable power (cosine losses, local slope tilt, and partial obscuration).",
        "Solar disk model uses circular segment intersection with local terrain horizon (Sun radius 696000 km from NAIF PCK pck00010.tpc).",
    ]

    def __init__(self, sun_radius_km: float = SUN_RADIUS_KM):
        self.sun_radius_km = float(sun_radius_km)

    def process_illumination_series(
        self,
        ephemeris_series: List[Dict[str, Any]],
        horizon_profile: List[Dict[str, Any]],
        horizon_interp_func,
    ) -> Dict[str, Any]:
        """
        Process ephemeris steps into terrain-aware illumination series,
        continuous windows, and summary totals.

        Args:
            ephemeris_series: list of dicts with keys:
                - timestamp: str
                - sun_azimuth_deg: float
                - sun_elevation_deg: float
                - sun_distance_km: float (optional, default 1.496e8)
            horizon_profile: list of {"azimuth_deg": ..., "horizon_elevation_deg": ...}
            horizon_interp_func: callable(profile, az_deg) -> float

        Returns:
            Dictionary with series, windows, totals, method, and disclaimers.
        """
        if not ephemeris_series:
            return {
                "series": [],
                "windows": {"any_part_lit": [], "fully_lit": []},
                "totals": {
                    "hours_any_part_lit": 0.0,
                    "hours_fully_lit": 0.0,
                    "hours_shadow": 0.0,
                    "total_simulation_hours": 0.0,
                    "number_of_windows": 0,
                    "shortest_window_hours": 0.0,
                    "longest_window_hours": 0.0,
                    "longest_continuous_shadow_hours": 0.0,
                },
                "disclaimers": self.DISCLAIMERS,
            }

        timestamps = []
        series_points = []
        any_part_signals = []   # (h_sun + R_sun) - h_horiz
        fully_lit_signals = []  # (h_sun - R_sun) - h_horiz

        for step in ephemeris_series:
            ts = step["timestamp"]
            timestamps.append(ts)
            sun_az = float(step.get("sun_azimuth_deg", step.get("sun_azimuth", 0.0)))
            sun_el = float(step.get("sun_elevation_deg", step.get("sun_elevation", 0.0)))
            sun_dist = float(step.get("sun_distance_km", 149597870.7))

            ang_radius = compute_solar_angular_radius_deg(sun_dist, self.sun_radius_km)
            h_horiz = horizon_interp_func(horizon_profile, sun_az)

            fraction, status = compute_illuminated_fraction(sun_el, h_horiz, ang_radius)

            # Signal for any part lit: upper limb > horizon
            any_part_signals.append((sun_el + ang_radius) - h_horiz)
            # Signal for fully lit: lower limb >= horizon
            fully_lit_signals.append((sun_el - ang_radius) - h_horiz)

            series_points.append({
                "timestamp": ts,
                "sun_azimuth": round(sun_az, 2),
                "sun_elevation": round(sun_el, 2),
                "sun_azimuth_deg": round(sun_az, 2),
                "sun_elevation_deg": round(sun_el, 2),
                "horizon_elevation_at_sun_azimuth": round(h_horiz, 2),
                "sun_angular_radius_deg": round(ang_radius, 4),
                "sun_distance_km": round(sun_dist, 2),
                "illuminated_fraction": round(fraction, 4),
                "status": status,
            })

        # Calculate simulation duration matching ephemeris steps
        total_sim_hours = round(len(ephemeris_series) * (30.0 / 60.0), 2)
        step_sec = 1800.0
        if len(timestamps) >= 2:
            dt_start = parse_iso_timestamp(timestamps[0])
            dt_end = parse_iso_timestamp(timestamps[-1])
            step_sec = (parse_iso_timestamp(timestamps[1]) - dt_start).total_seconds()
            total_sim_hours = round(len(timestamps) * (step_sec / 3600.0), 2)

        # Refine contiguous windows
        any_part_windows_raw = refine_continuous_windows(
            timestamps, any_part_signals, threshold=0.0, inclusive_ge=False, step_sec=step_sec
        )
        fully_lit_windows_raw = refine_continuous_windows(
            timestamps, fully_lit_signals, threshold=0.0, inclusive_ge=True, step_sec=step_sec
        )

        # Clean windows output (strip internal start_sec / end_sec for response)
        any_part_windows = [
            {"start": w["start"], "end": w["end"], "duration_hours": w["duration_hours"]}
            for w in any_part_windows_raw
        ]
        fully_lit_windows = [
            {"start": w["start"], "end": w["end"], "duration_hours": w["duration_hours"]}
            for w in fully_lit_windows_raw
        ]

        hours_any_part_lit = round(sum(w["duration_hours"] for w in any_part_windows), 4)
        hours_fully_lit = round(sum(w["duration_hours"] for w in fully_lit_windows), 4)
        hours_shadow = round(max(0.0, total_sim_hours - hours_any_part_lit), 4)

        num_windows = len(any_part_windows)
        shortest_w = round(min(w["duration_hours"] for w in any_part_windows), 4) if any_part_windows else 0.0
        longest_w = round(max(w["duration_hours"] for w in any_part_windows), 4) if any_part_windows else 0.0

        # Calculate shadow periods and longest continuous shadow duration
        shadow_periods: List[Dict[str, Any]] = []
        longest_shadow = 0.0
        total_sec = total_sim_hours * 3600.0

        if not any_part_windows_raw:
            longest_shadow = total_sim_hours
            sim_end_dt = datetime.fromtimestamp(dt_start.timestamp() + total_sec, tz=timezone.utc)
            shadow_periods.append({
                "start": timestamps[0],
                "end": format_iso_timestamp(sim_end_dt),
                "duration_hours": round(total_sim_hours, 4),
            })
        else:
            # Leading shadow before first window
            if any_part_windows_raw[0]["start_sec"] > 0.0:
                dur = any_part_windows_raw[0]["start_sec"] / 3600.0
                shadow_periods.append({
                    "start": timestamps[0],
                    "end": any_part_windows_raw[0]["start"],
                    "duration_hours": round(dur, 4),
                })
            # Intermediate shadows between lit windows
            for k in range(len(any_part_windows_raw) - 1):
                gap_sec = any_part_windows_raw[k + 1]["start_sec"] - any_part_windows_raw[k]["end_sec"]
                if gap_sec > 0.0:
                    dur = gap_sec / 3600.0
                    shadow_periods.append({
                        "start": any_part_windows_raw[k]["end"],
                        "end": any_part_windows_raw[k + 1]["start"],
                        "duration_hours": round(dur, 4),
                    })
            # Trailing shadow after last window
            if any_part_windows_raw[-1]["end_sec"] < total_sec:
                dur = (total_sec - any_part_windows_raw[-1]["end_sec"]) / 3600.0
                sim_end_dt = datetime.fromtimestamp(dt_start.timestamp() + total_sec, tz=timezone.utc)
                shadow_periods.append({
                    "start": any_part_windows_raw[-1]["end"],
                    "end": format_iso_timestamp(sim_end_dt),
                    "duration_hours": round(dur, 4),
                })

            if shadow_periods:
                longest_shadow = max(p["duration_hours"] for p in shadow_periods)

        totals = {
            "hours_any_part_lit": round(hours_any_part_lit, 2),
            "hours_fully_lit": round(hours_fully_lit, 2),
            "hours_shadow": round(hours_shadow, 2),
            "total_simulation_hours": round(total_sim_hours, 2),
            "number_of_windows": num_windows,
            "shortest_window_hours": round(shortest_w, 2),
            "longest_window_hours": round(longest_w, 2),
            "longest_continuous_shadow_hours": round(longest_shadow, 2),
            "boundary_refinement_method": "linear interpolation between time steps",
        }

        return {
            "series": series_points,
            "windows": {
                "any_part_lit": any_part_windows,
                "fully_lit": fully_lit_windows,
            },
            "shadow_periods": shadow_periods,
            "totals": totals,
            "method": self.METHOD_NAME,
            "disclaimers": self.DISCLAIMERS,
        }
