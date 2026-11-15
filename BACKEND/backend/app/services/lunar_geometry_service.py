"""
Lunar Geometry Service (Phase B3a: LL-11 to LL-13, LL-17, LL-18).

Calculates topocentric Sun and Earth vectors in the local East-North-Up (ENU) frame
at a candidate lunar landing site using SPICE (SpiceyPy).
Implements flat horizon (elevation > 0 deg) geometric visibility and contiguous windows.
"""

import os
import math
import datetime
import threading
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

try:
    import spiceypy as spice
    SPICE_AVAILABLE = True
except ImportError:
    SPICE_AVAILABLE = False


# Process-wide recursive lock to serialize non-thread-safe CSPICE calls
SPICE_LOCK = threading.RLock()


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KERNELS_DIR = os.path.join(PROJECT_ROOT, "storage", "kernels")

REQUIRED_KERNELS = [
    "naif0012.tls",
    "de421.bsp",
    "pck00010.tpc",
    "moon_pa_de421_1900-2050.bpc",
    "moon_080317.tf",
    "moon_assoc_me.tf",
]

FRAME_NAME = "MOON_ME_DE421"
MOON_RADIUS_KM = 1737.4  # from DEM label A_AXIS_RADIUS

DISCLAIMERS = [
    "Geometric visibility is not a guaranteed radio link.",
    "Sunlight is not guaranteed electrical power.",
    "Flat horizon ignores terrain shadowing; actual visibility depends on local topography.",
    "Planning support tool, not safety certification.",
    "Sun and Earth are treated as point sources at their barycenter/center.",
]


class MissingKernelsError(Exception):
    """Raised when required SPICE kernels are not found on disk."""
    pass


class KernelManager:
    """Manages loading and checking SPICE kernels safely and idempotently."""

    _loaded = False
    _lock = threading.RLock()

    @classmethod
    def check_kernels(cls) -> List[str]:
        missing = []
        for k in REQUIRED_KERNELS:
            path = os.path.join(KERNELS_DIR, k)
            if not os.path.exists(path):
                missing.append(k)
        return missing

    @classmethod
    def are_kernels_available(cls) -> bool:
        return len(cls.check_kernels()) == 0

    @classmethod
    def load_kernels(cls) -> None:
        if not SPICE_AVAILABLE:
            raise RuntimeError("SpiceyPy is not installed.")
        with cls._lock:
            if cls._loaded:
                return
            missing = cls.check_kernels()
            if missing:
                raise MissingKernelsError(
                    f"Missing required SPICE kernels: {missing}. "
                    "Please run scripts/download_kernels.py to download required generic kernels."
                )
            with SPICE_LOCK:
                spice.kclear()
                for k in REQUIRED_KERNELS:
                    path = os.path.join(KERNELS_DIR, k)
                    spice.furnsh(path)
                cls._loaded = True

    @classmethod
    def unload_kernels(cls) -> None:
        with cls._lock:
            if SPICE_AVAILABLE:
                with SPICE_LOCK:
                    spice.kclear()
            cls._loaded = False


def safe_str2et(date_str: str) -> float:
    """Parse UTC date/time string to Ephemeris Time (ET) safely under SPICE_LOCK."""
    if not SPICE_AVAILABLE:
        raise RuntimeError("SpiceyPy is not installed.")
    KernelManager.load_kernels()
    with SPICE_LOCK:
        return float(spice.str2et(date_str))


def compute_local_enu_basis(lat_deg: float, lon_deg: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute orthonormal East, North, Up unit vectors in MOON_ME_DE421 frame
    for a site given its planetocentric latitude and east-positive longitude (deg).

    Up:    (cos(lat)*cos(lon), cos(lat)*sin(lon), sin(lat))
    East:  (-sin(lon), cos(lon), 0)
    North: (-sin(lat)*cos(lon), -sin(lat)*sin(lon), cos(lat))
    """
    lat_rad = math.radians(lat_deg)
    lon_rad = math.radians(lon_deg)

    u_hat = np.array([
        math.cos(lat_rad) * math.cos(lon_rad),
        math.cos(lat_rad) * math.sin(lon_rad),
        math.sin(lat_rad),
    ], dtype=np.float64)

    e_hat = np.array([
        -math.sin(lon_rad),
        math.cos(lon_rad),
        0.0,
    ], dtype=np.float64)

    n_hat = np.array([
        -math.sin(lat_rad) * math.cos(lon_rad),
        -math.sin(lat_rad) * math.sin(lon_rad),
        math.cos(lat_rad),
    ], dtype=np.float64)

    return e_hat, n_hat, u_hat


def vector_to_az_el(vec: np.ndarray, e_hat: np.ndarray, n_hat: np.ndarray, u_hat: np.ndarray) -> Tuple[float, float]:
    """
    Project a 3D vector onto local ENU frame and compute azimuth and elevation (deg).
    Azimuth: degrees clockwise from North toward East [0, 360).
    Elevation: degrees above horizon [-90, +90].
    """
    v_e = float(np.dot(vec, e_hat))
    v_n = float(np.dot(vec, n_hat))
    v_u = float(np.dot(vec, u_hat))

    d_h = math.sqrt(v_e ** 2 + v_n ** 2)
    el_deg = math.degrees(math.atan2(v_u, d_h))
    az_deg = math.degrees(math.atan2(v_e, v_n)) % 360.0

    return az_deg, el_deg


def detect_windows(series: List[Dict[str, Any]], key: str, step_minutes: int) -> List[Dict[str, Any]]:
    """
    Detect contiguous periods where series[i][key] == True.
    Returns list of {"start": ISO, "end": ISO, "duration_hours": float}.
    """
    windows = []
    in_window = False
    start_ts = None
    last_ts = None
    count = 0

    step_hours = step_minutes / 60.0

    for pt in series:
        val = pt.get(key, False)
        ts = pt["timestamp"]
        if val:
            if not in_window:
                in_window = True
                start_ts = ts
                count = 1
            else:
                count += 1
            last_ts = ts
        else:
            if in_window:
                windows.append({
                    "start": start_ts,
                    "end": last_ts,
                    "duration_hours": round(count * step_hours, 2),
                    "steps": count,
                })
                in_window = False
                start_ts = None
                last_ts = None
                count = 0

    if in_window:
        windows.append({
            "start": start_ts,
            "end": last_ts,
            "duration_hours": round(count * step_hours, 2),
            "steps": count,
        })

    return windows


class LunarGeometryService:
    """
    Service for calculating lunar topocentric solar and terrestrial geometric visibility.
    """

    def __init__(self):
        pass

    def calculate_geometry(
        self,
        lat_deg: float,
        lon_deg: float,
        elevation_m: float,
        start_utc: str,
        days: int = 30,
        step_minutes: int = 30,
    ) -> Dict[str, Any]:
        """
        Compute topocentric sun and earth azimuth and elevation series over the given time range.
        """
        if not SPICE_AVAILABLE:
            raise RuntimeError("SpiceyPy is not installed.")

        KernelManager.load_kernels()

        # Parse start_utc safely under SPICE_LOCK
        try:
            with SPICE_LOCK:
                et_start = spice.str2et(start_utc)
        except Exception as e:
            raise ValueError(f"Invalid UTC start date/time '{start_utc}': {e}")

        # Compute observer position in MOON_ME_DE421
        r_km = MOON_RADIUS_KM + (elevation_m / 1000.0)
        lat_rad = math.radians(lat_deg)
        lon_rad = math.radians(lon_deg)
        p_obs = np.array([
            r_km * math.cos(lat_rad) * math.cos(lon_rad),
            r_km * math.cos(lat_rad) * math.sin(lon_rad),
            r_km * math.sin(lat_rad),
        ], dtype=np.float64)

        # Local ENU unit vectors
        e_hat, n_hat, u_hat = compute_local_enu_basis(lat_deg, lon_deg)

        total_steps = int(round((days * 24 * 60) / step_minutes))
        step_sec = step_minutes * 60.0

        # Execute pure SPICE ephemeris queries under SPICE_LOCK to ensure thread-safety
        spice_raw = []
        with SPICE_LOCK:
            for i in range(total_steps):
                et = et_start + i * step_sec
                utc_str = spice.et2utc(et, "ISOC", 0) + "Z"
                p_sun, _ = spice.spkpos("SUN", et, FRAME_NAME, "LT+S", "MOON")
                p_earth, _ = spice.spkpos("EARTH", et, FRAME_NAME, "LT+S", "MOON")
                spice_raw.append((utc_str, p_sun, p_earth))

        series = []
        sun_up_count = 0
        earth_up_count = 0
        joint_up_count = 0

        # Vector algebra and horizon checks run outside SPICE_LOCK
        for utc_str, p_sun, p_earth in spice_raw:
            # Sun position relative to Moon center
            v_sun = np.array(p_sun, dtype=np.float64) - p_obs
            sun_az, sun_el = vector_to_az_el(v_sun, e_hat, n_hat, u_hat)

            # Earth position relative to Moon center
            v_earth = np.array(p_earth, dtype=np.float64) - p_obs
            earth_az, earth_el = vector_to_az_el(v_earth, e_hat, n_hat, u_hat)

            sun_vis = sun_el > 0.0
            earth_vis = earth_el > 0.0
            joint_vis = sun_vis and earth_vis

            if sun_vis:
                sun_up_count += 1
            if earth_vis:
                earth_up_count += 1
            if joint_vis:
                joint_up_count += 1

            series.append({
                "timestamp": utc_str,
                "sun_azimuth_deg": round(sun_az, 2),
                "sun_elevation_deg": round(sun_el, 2),
                "earth_azimuth_deg": round(earth_az, 2),
                "earth_elevation_deg": round(earth_el, 2),
                "sun_distance_km": round(float(np.linalg.norm(v_sun)), 2),
                "earth_distance_km": round(float(np.linalg.norm(v_earth)), 2),
                "sun_visible": sun_vis,
                "earth_visible": earth_vis,
                "joint_visible": joint_vis,
            })

        step_hours = step_minutes / 60.0
        totals = {
            "sunlight_hours": round(sun_up_count * step_hours, 2),
            "earth_visible_hours": round(earth_up_count * step_hours, 2),
            "joint_sunlight_and_earth_visible_hours": round(joint_up_count * step_hours, 2),
            "total_simulation_hours": round(total_steps * step_hours, 2),
            "sunlight_fraction": round(sun_up_count / total_steps, 4) if total_steps > 0 else 0.0,
            "earth_visible_fraction": round(earth_up_count / total_steps, 4) if total_steps > 0 else 0.0,
        }

        windows = {
            "sunlight": detect_windows(series, "sun_visible", step_minutes),
            "earth_visibility": detect_windows(series, "earth_visible", step_minutes),
            "joint_visibility": detect_windows(series, "joint_visible", step_minutes),
        }

        return {
            "frame": FRAME_NAME,
            "method": "SPICE geometric, flat horizon",
            "kernels_used": REQUIRED_KERNELS,
            "observer_elevation_m": round(elevation_m, 2),
            "reference_sphere_radius_km": MOON_RADIUS_KM,
            "series": series,
            "windows": windows,
            "totals": totals,
            "disclaimers": DISCLAIMERS,
        }


_lunar_geometry_service_singleton: Optional[LunarGeometryService] = None


def get_lunar_geometry_service() -> LunarGeometryService:
    global _lunar_geometry_service_singleton
    if _lunar_geometry_service_singleton is None:
        _lunar_geometry_service_singleton = LunarGeometryService()
    return _lunar_geometry_service_singleton
