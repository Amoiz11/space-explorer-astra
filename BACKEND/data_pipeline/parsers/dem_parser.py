"""
DEM parser for PDS3 binary image files.

Reads parameters EXCLUSIVELY from the .lbl label (sample type, byte order,
lines, line samples, scaling factor, offset). Never assumes them.

DSMAP_POLAR.CAT formula (fetched from NASA PDS Geosciences Node):
  HEIGHT = DN * SCALING_FACTOR
  PLANETARY_RADIUS = (DN * SCALING_FACTOR) + OFFSET

No-data value: not stated in the label for this product; suspicious fill
values (int16 extremes -32768 or 32767) are reported but not masked by
default because the label provides no authoritative value.
"""

import os
import re
import struct
import numpy as np
from typing import Dict, Any, Optional


class DEMParser:
    """
    Parse a PDS3 .IMG binary DEM using parameters read from its .lbl label.
    Pure Python + numpy; no GDAL or rasterio.
    """

    # Sample type mapping: PDS3 SAMPLE_TYPE -> numpy dtype string
    SAMPLE_TYPE_MAP = {
        "LSB_INTEGER": "<i2",   # 16-bit signed, little-endian
        "MSB_INTEGER": ">i2",   # 16-bit signed, big-endian
        "LSB_UNSIGNED_INTEGER": "<u2",
        "MSB_UNSIGNED_INTEGER": ">u2",
        "PC_INTEGER": "<i2",    # alias used by some PDS products
        "MAC_INTEGER": ">i2",
        "SUN_INTEGER": ">i2",
        "LSB_BIT_STRING": "<u2",
        "REAL": "<f4",
        "PC_REAL": "<f4",
        "IEEE_REAL": ">f4",
        "SUN_REAL": ">f4",
        "FLOAT": "<f4",
        "DOUBLE": "<f8",
    }

    # Suspicious fill sentinels to report (int16 extremes)
    FILL_SENTINELS_I16 = {-32768, 32767}

    def parse_label(self, lbl_path: str) -> Dict[str, Any]:
        """
        Parse a PDS3 .lbl file and return all needed parameters.
        Raises ValueError if a required parameter is missing.
        """
        with open(lbl_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        # Strip comments /* ... */
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

        kv: Dict[str, str] = {}
        current_key: Optional[str] = None
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped == "END":
                continue
            m = re.match(r"^\s*([A-Za-z0-9_:\^]+)\s*=\s*(.*)$", line)
            if m:
                current_key = m.group(1).strip()
                val = m.group(2).strip().strip('"').strip("'")
                kv[current_key] = val
            elif current_key and stripped:
                kv[current_key] = kv[current_key] + " " + stripped.strip('"').strip("'")

        def _require(key: str) -> str:
            v = kv.get(key)
            if v is None or v.upper() in ("N/A", "NULL", ""):
                raise ValueError(
                    f"DEMParser: required label parameter '{key}' is missing or N/A in {lbl_path}"
                )
            return v

        def _float(key: str) -> float:
            raw = _require(key)
            m2 = re.search(r"[+-]?\d+\.?\d*(?:[eE][+-]?\d+)?", raw)
            if not m2:
                raise ValueError(f"DEMParser: cannot parse float from {key} = '{raw}'")
            return float(m2.group())

        def _int(key: str) -> int:
            return int(_float(key))

        lines = _int("LINES")
        samples = _int("LINE_SAMPLES")
        sample_bits = _int("SAMPLE_BITS")
        sample_type_raw = _require("SAMPLE_TYPE")
        scaling_factor = _float("SCALING_FACTOR")
        offset = _float("OFFSET")
        unit = kv.get("UNIT", "not stated in label")

        # Map sample type to numpy dtype
        sample_type_key = sample_type_raw.upper()
        if sample_type_key not in self.SAMPLE_TYPE_MAP:
            raise ValueError(
                f"DEMParser: unsupported SAMPLE_TYPE '{sample_type_raw}'. "
                f"Known types: {list(self.SAMPLE_TYPE_MAP.keys())}"
            )
        dtype_str = self.SAMPLE_TYPE_MAP[sample_type_key]

        # Adjust for bit width  
        if sample_bits == 8:
            dtype_str = dtype_str.replace("i2", "i1").replace("u2", "u1")
        elif sample_bits == 32:
            dtype_str = dtype_str.replace("i2", "i4").replace("u2", "u4")

        # Projection parameters
        map_scale_raw = kv.get("MAP_SCALE")
        map_scale = None
        if map_scale_raw:
            m2 = re.search(r"[+-]?\d+\.?\d*", map_scale_raw)
            if m2:
                map_scale = float(m2.group())

        return {
            "lines": lines,
            "line_samples": samples,
            "sample_bits": sample_bits,
            "sample_type": sample_type_raw,
            "dtype": dtype_str,
            "scaling_factor": scaling_factor,
            "offset_m": offset,
            "unit": unit,
            "map_scale": map_scale,
            "derived_minimum": kv.get("DERIVED_MINIMUM"),
            "derived_maximum": kv.get("DERIVED_MAXIMUM"),
        }

    def read_img(self, img_path: str, label: Dict[str, Any]) -> np.ndarray:
        """
        Read the binary .IMG file into a numpy array of raw DN values.
        Uses only the parameters supplied from the label.
        """
        lines = label["lines"]
        samples = label["line_samples"]
        dtype = np.dtype(label["dtype"])
        expected_bytes = lines * samples * dtype.itemsize

        actual_size = os.path.getsize(img_path)
        if actual_size < expected_bytes:
            raise ValueError(
                f"DEMParser: .IMG file is {actual_size} bytes; label says "
                f"{lines}×{samples}×{dtype.itemsize} = {expected_bytes} bytes required."
            )

        raw = np.fromfile(img_path, dtype=dtype)
        # Some PDS products have appended bytes; take exactly what the label says
        raw = raw[: lines * samples].reshape(lines, samples)
        return raw

    def to_elevation(self, dn_array: np.ndarray, label: Dict[str, Any]) -> np.ndarray:
        """
        Convert DN → elevation in metres relative to reference sphere.
        HEIGHT = DN * SCALING_FACTOR  (from DSMAP_POLAR.CAT and label NOTE block)
        """
        return dn_array.astype(np.float64) * label["scaling_factor"]

    def to_planetary_radius(self, dn_array: np.ndarray, label: Dict[str, Any]) -> np.ndarray:
        """
        Convert DN → planetary radius in metres.
        PLANETARY_RADIUS = (DN * SCALING_FACTOR) + OFFSET
        """
        return dn_array.astype(np.float64) * label["scaling_factor"] + label["offset_m"]

    def report(
        self,
        img_path: str,
        lbl_path: str,
        save_processed: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full pipeline: read label, load IMG, convert, report statistics.
        Optionally save elevation array as .npy to save_processed path.
        """
        label = self.parse_label(lbl_path)
        dn = self.read_img(img_path, label)
        elev = self.to_elevation(dn, label)

        lines, samples = elev.shape
        pixel_size_m = label.get("map_scale")

        # Suspicious fill detection (int16 extremes; label states no fill value)
        dn_i16 = dn.astype(np.int64)
        fill_counts = {}
        for sentinel in self.FILL_SENTINELS_I16:
            count = int(np.sum(dn_i16 == sentinel))
            if count:
                fill_counts[sentinel] = count

        total_pixels = lines * samples
        # No authoritative no-data value → report fill suspicion only
        no_data_pixels = sum(fill_counts.values())
        no_data_pct = 100.0 * no_data_pixels / total_pixels if total_pixels else 0.0

        result = {
            "shape": (lines, samples),
            "pixel_size_m": pixel_size_m,
            "dtype": label["dtype"],
            "sample_type": label["sample_type"],
            "scaling_factor": label["scaling_factor"],
            "offset_m": label["offset_m"],
            "unit": label["unit"],
            "no_data_note": "not stated in label",
            "suspicious_fill_sentinels": fill_counts,
            "suspicious_fill_count": no_data_pixels,
            "suspicious_fill_pct": round(no_data_pct, 4),
            "elev_min_m": float(np.min(elev)),
            "elev_max_m": float(np.max(elev)),
            "elev_mean_m": float(np.mean(elev)),
        }

        if save_processed:
            os.makedirs(os.path.dirname(save_processed), exist_ok=True)
            np.save(save_processed, elev.astype(np.float32))
            result["saved_to"] = save_processed

        return result
