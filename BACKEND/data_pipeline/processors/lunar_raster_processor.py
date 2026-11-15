"""
Lunar raster processor and sidecar generator for MMGIS layers (Phase B5b).
Generates downsampled preview PNGs and JSON sidecars for LOLA DEM and Slope.
"""

import json
import math
import os
from typing import Dict, Any, Optional
import numpy as np
from PIL import Image

STORAGE_PROCESSED = os.path.abspath("storage/processed")
DEM_NPY_PATH = os.path.join(STORAGE_PROCESSED, "lunar", "ldem_75s_240m_elev.npy")

LUNAR_DEM_PNG = os.path.join(STORAGE_PROCESSED, "lunar_dem.png")
LUNAR_DEM_JSON = os.path.join(STORAGE_PROCESSED, "lunar_dem.json")
LUNAR_SLOPE_PNG = os.path.join(STORAGE_PROCESSED, "lunar_slope.png")
LUNAR_SLOPE_JSON = os.path.join(STORAGE_PROCESSED, "lunar_slope.json")

# Metadata exactly as stated in the LOLA DEM label (storage/raw/lunar/ldem_75s_240m.lbl)
LOLA_LABEL_PROJECTION: Dict[str, Any] = {
    "map_projection_type": "POLAR STEREOGRAPHIC",
    "coordinate_system_name": "MEAN EARTH/POLAR AXIS OF DE421",
    "coordinate_system_type": "BODY-FIXED ROTATING",
    "keyword_latitude_type": "PLANETOCENTRIC",
    "positive_longitude_direction": "EAST",
    "center_latitude": -90.0,
    "center_longitude": 0.0,
    "reference_latitude": "N/A",
    "reference_longitude": "N/A",
    "first_standard_parallel": "N/A",
    "second_standard_parallel": "N/A",
    "map_projection_rotation": 0.0,
    "map_resolution_pix_per_deg": 126.347,
    "map_scale_m_per_pix": 240.0,
    "a_axis_radius_km": 1737.4,
    "b_axis_radius_km": 1737.4,
    "c_axis_radius_km": 1737.4,
    "reference_radius_m": 1737400.0,
    "line_projection_offset_pix": 1905.5,
    "sample_projection_offset_pix": 1905.5,
    "data_set_id": "LRO-L-LOLA-4-GDR-V1.0",
    "source_product_id": "lola-dem-75s-240m",
}

LOLA_LABEL_BOUNDS: Dict[str, Any] = {
    "minimum_latitude_deg": -90.0,
    "maximum_latitude_deg": -75.0,
    "westernmost_longitude": "N/A",
    "easternmost_longitude": "N/A",
    "x_min_m": -457320.0,
    "x_max_m": 457320.0,
    "y_min_m": -457320.0,
    "y_max_m": 457320.0,
}

COORDINATE_REFERENCE_NOTE = (
    "Moon lunar polar coordinates (MOON_ME_DE421). Frame is Moon mean-Earth frame, "
    "planetocentric latitude, east-positive longitude. Not an Earth coordinate system. "
    "Polar stereographic projection true at south pole (-90 deg)."
)


def generate_lunar_rasters_and_sidecars(downsample_factor: int = 8) -> None:
    """
    Generate downsampled PNGs and sidecars for DEM and Slope if not already present.
    """
    os.makedirs(STORAGE_PROCESSED, exist_ok=True)

    if not os.path.exists(DEM_NPY_PATH):
        return

    # 1. Load elevation array
    elev_full = np.load(DEM_NPY_PATH)
    rows_full, cols_full = elev_full.shape
    sub_elev = elev_full[::downsample_factor, ::downsample_factor].astype(np.float64)
    h_sub, w_sub = sub_elev.shape

    sub_pixel_size_m = 240.0 * float(downsample_factor)

    # 2. DEM PNG
    min_elev = float(np.min(sub_elev))
    max_elev = float(np.max(sub_elev))
    elev_norm = np.clip((sub_elev - min_elev) / (max_elev - min_elev) * 255.0, 0, 255).astype(np.uint8)
    img_dem = Image.fromarray(elev_norm)
    img_dem.save(LUNAR_DEM_PNG, format="PNG")

    dem_sidecar: Dict[str, Any] = {
        "layer_id": "lunar_dem",
        "name": "Lunar LOLA DEM (South Polar)",
        "source_product_id": "lola-dem-75s-240m",
        "data_file": "storage/processed/lunar_dem.png",
        "projection": LOLA_LABEL_PROJECTION,
        "bounds": LOLA_LABEL_BOUNDS,
        "pixel_size": {
            "width": w_sub,
            "height": h_sub,
            "downsample_factor": downsample_factor,
            "pixel_resolution_m": sub_pixel_size_m,
            "original_resolution_m": 240.0,
            "units": "meters/pixel",
        },
        "colour_scale": {
            "type": "linear",
            "min_value": round(min_elev, 2),
            "max_value": round(max_elev, 2),
            "palette": "grayscale_8bit",
            "min_color": "#000000",
            "max_color": "#FFFFFF",
            "units": "meters",
        },
        "units": "meters relative to 1737.4 km reference sphere",
        "coordinate_reference_note": COORDINATE_REFERENCE_NOTE,
        "disclaimer": (
            "Downsampled preview raster (1920 m/pixel) from 240 m LOLA DEM. "
            "Planning support tool, not safety certification. "
            "A 240 m DEM cannot represent sub-resolution micro-hazards or boulders."
        ),
    }
    with open(LUNAR_DEM_JSON, "w", encoding="utf-8") as f:
        json.dump(dem_sidecar, f, indent=2)

    # 3. Slope computation via Horn finite difference on sub_elev
    # dz/dx and dz/dy with pixel spacing = sub_pixel_size_m
    padded = np.pad(sub_elev, pad_width=1, mode="edge")
    z1 = padded[:-2, :-2]
    z2 = padded[:-2, 1:-1]
    z3 = padded[:-2, 2:]
    z4 = padded[1:-1, :-2]
    z6 = padded[1:-1, 2:]
    z7 = padded[2:, :-2]
    z8 = padded[2:, 1:-1]
    z9 = padded[2:, 2:]

    dz_dx = ((z3 + 2.0 * z6 + z9) - (z1 + 2.0 * z4 + z7)) / (8.0 * sub_pixel_size_m)
    dz_dy = ((z7 + 2.0 * z8 + z9) - (z1 + 2.0 * z2 + z3)) / (8.0 * sub_pixel_size_m)
    slope_rad = np.arctan(np.sqrt(dz_dx * dz_dx + dz_dy * dz_dy))
    slope_deg = np.degrees(slope_rad)

    min_slope = float(np.min(slope_deg))
    max_slope = float(np.max(slope_deg))
    # Clip for display 0 to 30 deg
    slope_display_max = 30.0
    slope_norm = np.clip(slope_deg / slope_display_max * 255.0, 0, 255).astype(np.uint8)
    img_slope = Image.fromarray(slope_norm)
    img_slope.save(LUNAR_SLOPE_PNG, format="PNG")

    slope_sidecar: Dict[str, Any] = {
        "layer_id": "lunar_slope",
        "name": "Lunar LOLA Slope (South Polar)",
        "source_product_id": "lola-dem-75s-240m",
        "data_file": "storage/processed/lunar_slope.png",
        "projection": LOLA_LABEL_PROJECTION,
        "bounds": LOLA_LABEL_BOUNDS,
        "pixel_size": {
            "width": w_sub,
            "height": h_sub,
            "downsample_factor": downsample_factor,
            "pixel_resolution_m": sub_pixel_size_m,
            "original_resolution_m": 240.0,
            "units": "meters/pixel",
        },
        "colour_scale": {
            "type": "linear",
            "min_value": 0.0,
            "max_value": slope_display_max,
            "actual_data_min": round(min_slope, 3),
            "actual_data_max": round(max_slope, 3),
            "palette": "grayscale_8bit",
            "min_color": "#000000",
            "max_color": "#FFFFFF",
            "units": "degrees",
        },
        "units": "degrees (Horn 1981 finite-difference slope)",
        "coordinate_reference_note": COORDINATE_REFERENCE_NOTE,
        "disclaimer": (
            "Derived slope from downsampled LOLA DEM. "
            "Slopes derived at 1920 m baseline differ from 240 m baseline and cannot resolve "
            "steep localized crater walls, rocks or boulders. Planning support tool, not safety certification."
        ),
    }
    with open(LUNAR_SLOPE_JSON, "w", encoding="utf-8") as f:
        json.dump(slope_sidecar, f, indent=2)


def get_sidecar_data(layer_id: str) -> Optional[Dict[str, Any]]:
    """Return JSON sidecar dict for a lunar raster layer."""
    clean = layer_id.lower().replace("-", "_")
    if clean.endswith(".json"):
        clean = clean[:-5]
    if clean == "lunar_dem":
        path = LUNAR_DEM_JSON
    elif clean == "lunar_slope":
        path = LUNAR_SLOPE_JSON
    else:
        return None

    if not os.path.exists(path):
        generate_lunar_rasters_and_sidecars()

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_raster_png_path(layer_id: str) -> Optional[str]:
    """Return PNG path for a lunar raster layer."""
    clean = layer_id.lower().replace("-", "_")
    if clean.endswith(".png"):
        clean = clean[:-4]
    if clean == "lunar_dem":
        path = LUNAR_DEM_PNG
    elif clean == "lunar_slope":
        path = LUNAR_SLOPE_PNG
    else:
        return None

    if not os.path.exists(path):
        generate_lunar_rasters_and_sidecars()

    if os.path.exists(path):
        return path
    return None
