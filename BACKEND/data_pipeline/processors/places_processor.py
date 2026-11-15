from typing import Dict, Any, List, Optional
from datetime import datetime

from data_pipeline.processors.sclk_converter import sclk_to_utc, get_provenance_metadata

PLACES_STRUCTURED_COORDINATE_FRAME = (
    "landing_x/y/z: SITE 1 relative frame (+X north, +Y east, +Z down); "
    "latitude/longitude: planetocentric, east-positive, as documented in the PLACES SIS. "
    "Mars body-fixed frame name not stated in the label."
)

class PlacesProcessor:
    def __init__(self, metadata: Dict[str, Any] = None):
        self.metadata = metadata or {}
        # Documented structured coordinate frame text
        self.coordinate_frame = PLACES_STRUCTURED_COORDINATE_FRAME

    def process_record(self, row: Dict[str, Any], product_id: str) -> Dict[str, Any]:
        """Transform a validated row into location data structure."""
        lat = float(row["planetocentric_latitude"])
        lon = float(row["longitude"])
        frame_type = str(row.get("frame", "")).strip().upper()

        def parse_float_safe(key: str) -> Optional[float]:
            val = row.get(key)
            if val is not None and str(val).strip() != "":
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None
            return None

        landing_x = parse_float_safe("landing_x")
        landing_y = parse_float_safe("landing_y")
        landing_z = parse_float_safe("landing_z")
        northing = parse_float_safe("northing")
        easting = parse_float_safe("easting")
        planetodetic_lat = parse_float_safe("planetodetic_latitude")
        elevation = parse_float_safe("elevation")
        areoid = parse_float_safe("areoid")
        radius = parse_float_safe("radius")
        roll = parse_float_safe("roll")
        pitch = parse_float_safe("pitch")
        yaw = parse_float_safe("yaw")

        def parse_int_safe(key: str) -> Optional[int]:
            val = row.get(key)
            if val is not None and str(val).strip() != "":
                try:
                    return int(float(val))
                except (ValueError, TypeError):
                    return None
            return None

        site = parse_int_safe("site")
        drive = parse_int_safe("drive")
        pose = parse_int_safe("pose")
        sol = parse_int_safe("sol")
        sclk = str(row.get("sclk", "")).strip()

        # Original coordinates keeping all original fields with units per field
        original_coords = {
            "values": [lat, lon],
            "units": "deg",
            "coordinate_frame": self.coordinate_frame,
            "site": {"value": site, "units": None},
            "drive": {"value": drive, "units": None},
            "pose": {"value": pose, "units": None},
            "sol": {"value": sol, "units": "sol"},
            "sclk": {"value": sclk, "units": "seconds"},
            "landing_x": {"value": landing_x, "units": "METER"},
            "landing_y": {"value": landing_y, "units": "METER"},
            "landing_z": {"value": landing_z, "units": "METER"},
            "planetocentric_latitude": {"value": lat, "units": "DEGREE"},
            "planetodetic_latitude": {"value": planetodetic_lat, "units": "DEGREE"},
            "longitude": {"value": lon, "units": "DEGREE"},
            "elevation": {"value": elevation, "units": "METER"},
            "northing": {"value": northing, "units": "METER"},
            "easting": {"value": easting, "units": "METER"},
            "areoid": {"value": areoid, "units": "METER"},
            "radius": {"value": radius, "units": "METER"},
            "frame": {"value": frame_type, "units": None},
            "attitude": {
                "roll": {"value": roll, "units": "DEGREE"},
                "pitch": {"value": pitch, "units": "DEGREE"},
                "yaw": {"value": yaw, "units": "DEGREE"},
                "quat_s": {"value": parse_float_safe("quat_s"), "units": None},
                "quat_v1": {"value": parse_float_safe("quat_v1"), "units": None},
                "quat_v2": {"value": parse_float_safe("quat_v2"), "units": None},
                "quat_v3": {"value": parse_float_safe("quat_v3"), "units": None},
            },
        }

        # SCLK to UTC conversion using NAIF SPICE kernel (m2020_sclkscet_refit_v19.tsc)
        observed_at = sclk_to_utc(sclk)
        if observed_at is not None:
            original_coords["time_conversion"] = get_provenance_metadata()

        # Rule: best_interp.csv rows are interpolated:
        # position_method: "interpolated", label: "Estimated", position_status: "estimated"
        # observed_at: converted from SCLK via SPICE; null if SCLK is outside coverage or reference (sol -1)
        # uncertainty: null (no real uncertainty exists in the product; method kept in position_method)
        return {
            "explorer_id": "perseverance",
            "observed_at": observed_at,
            "original_coordinates": original_coords,
            "coordinate_frame": self.coordinate_frame,
            "uncertainty": None,
            "product_id": product_id,
            "position_method": "interpolated (converted from SCLK via NAIF SPICE)" if observed_at else "interpolated",
            "position_status": "estimated",
            "label": "Estimated",
            "is_placeholder": False,
        }

    def process_batch(self, valid_records: List[Dict[str, Any]], product_id: str) -> List[Dict[str, Any]]:
        """Process a batch of validated records."""
        return [self.process_record(r, product_id) for r in valid_records]
