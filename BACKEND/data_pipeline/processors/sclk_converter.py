"""
Mars 2020 Spacecraft Clock (SCLK) to UTC Converter.

Converts SCLK ticks/seconds from Mars 2020 telemetry (PDS PLACES)
to Ephemeris Time (ET) and UTC using NAIF SPICE kernels:
  - naif0012.tls (leapseconds kernel)
  - m2020_168_sclkscet_refit_v19.tsc (Mars 2020 SCLK kernel)

NAIF Spacecraft ID for Mars 2020 Perseverance is -168.
"""

import os
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any

try:
    import spiceypy as spice
except ImportError:
    spice = None

_SPICE_LOCK = threading.RLock()
_KERNELS_LOADED = False

KERNEL_NAMES = ["naif0012.tls", "m2020_168_sclkscet_refit_v19.tsc"]
CONVERSION_METHOD = "SpiceyPy scs2e -> et2utc (ISOC)"
CONVERSION_NOTE = "converted from SCLK"
MARS2020_CLOCK_ID = -168


def get_default_kernel_paths() -> Dict[str, str]:
    """Resolve kernel paths relative to backend storage directory."""
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "storage", "kernels")
    )
    return {
        "lsk": os.path.join(base_dir, "naif0012.tls"),
        "sclk": os.path.join(base_dir, "m2020_168_sclkscet_refit_v19.tsc"),
    }


def ensure_kernels_loaded(lsk_path: str = None, sclk_path: str = None) -> bool:
    """Load required NAIF kernels if present on disk."""
    global _KERNELS_LOADED
    if spice is None:
        return False

    with _SPICE_LOCK:
        if _KERNELS_LOADED:
            return True

        paths = get_default_kernel_paths()
        lsk = lsk_path or paths["lsk"]
        sclk = sclk_path or paths["sclk"]

        if not (os.path.exists(lsk) and os.path.exists(sclk)):
            return False

        try:
            spice.furnsh(lsk)
            spice.furnsh(sclk)
            _KERNELS_LOADED = True
            return True
        except Exception:
            return False


def sclk_to_utc(
    sclk_val: Any,
    clock_id: int = MARS2020_CLOCK_ID,
    lsk_path: str = None,
    sclk_path: str = None,
) -> Optional[datetime]:
    """
    Convert an SCLK string or count to a Python datetime in UTC.
    Returns None if:
      - sclk_val is None, empty, or '0' (reference epoch)
      - kernels cannot be loaded
      - SCLK value is outside the kernel coverage or invalid
    """
    if sclk_val is None:
        return None

    sclk_str = str(sclk_val).strip()
    if not sclk_str or sclk_str == "0":
        return None

    if not ensure_kernels_loaded(lsk_path, sclk_path):
        return None

    with _SPICE_LOCK:
        try:
            et = spice.scs2e(clock_id, sclk_str)
            utc_str = spice.et2utc(et, "ISOC", 3)
            # Parse 'YYYY-MM-DDTHH:MM:SS.fff'
            # Remove trailing 'Z' if present
            clean_utc = utc_str.replace("Z", "")
            dt = datetime.fromisoformat(clean_utc).replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None


def get_provenance_metadata() -> Dict[str, Any]:
    """Return provenance dictionary for SCLK-to-UTC conversion."""
    return {
        "conversion_method": CONVERSION_METHOD,
        "kernels": KERNEL_NAMES,
        "clock_id": MARS2020_CLOCK_ID,
        "note": CONVERSION_NOTE,
    }
